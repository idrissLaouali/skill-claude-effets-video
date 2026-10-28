"""Lecture de la vidéo, détection du visage (YuNet) et détourage de la personne (MediaPipe Selfie Segmenter)."""
import json, math, os, subprocess
import numpy as np
import cv2
from .base import RACINE


def infos(chemin):
    """fps (plafonné à 30), durée, largeur, hauteur."""
    j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                   'stream=r_frame_rate,width,height:stream_tags=rotate:format=duration', '-of', 'json', chemin],
                                  capture_output=True, text=True, check=True).stdout)
    st = j['streams'][0]
    n, d = st['r_frame_rate'].split('/'); fps = min(float(n) / float(d or 1), 30.0)
    w, h = int(st['width']), int(st['height'])
    if str(st.get('tags', {}).get('rotate', '0')) in ('90', '270', '-90'): w, h = h, w
    return round(fps, 3), float(j['format']['duration']), w, h


def images(chemin, W, H, fps):
    """Générateur d'images RGB uint8 à la taille demandée."""
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', chemin, '-vf', f'fps={fps},scale={W}:{H}:flags=bicubic,format=rgb24',
                          '-f', 'rawvideo', '-'], stdout=subprocess.PIPE, bufsize=10 ** 8)
    n = W * H * 3
    try:
        while True:
            b = p.stdout.read(n)
            if len(b) < n: break
            yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    finally:
        if p.poll() is None: p.kill()
        p.stdout.close(); p.wait()


def _affiner(guide, m, r=8, eps=2e-3):
    """Filtre guidé : colle les bords du masque aux vrais contours (cheveux, épaules)."""
    moy = lambda x: cv2.boxFilter(x, -1, (2 * r + 1, 2 * r + 1))
    mi, mm = moy(guide), moy(m)
    a = (moy(guide * m) - mi * mm) / (moy(guide * guide) - mi * mi + eps)
    b = mm - a * mi
    return np.clip(moy(a) * guide + moy(b), 0, 1)


class Suivi:
    def __init__(self, w, h):
        import mediapipe as mp
        from mediapipe.tasks.python import vision
        from mediapipe.tasks.python.core.base_options import BaseOptions
        self.mp = mp
        opts = vision.ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=os.path.join(RACINE, 'models', 'selfie_segmenter.tflite')),
            running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True, output_category_mask=False)
        self.decoupe = vision.ImageSegmenter.create_from_options(opts)
        self.visages = cv2.FaceDetectorYN.create(os.path.join(RACINE, 'models', 'yunet.onnx'), '', (w, h), 0.6, 0.3, 20)
        self.precedent = None

    def oublier(self):
        self.precedent = None

    def __call__(self, rgb, ms):
        im = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        m = self.decoupe.segment_for_video(im, ms).confidence_masks[-1].numpy_view().astype(np.float32)
        m = m.reshape(m.shape[0], m.shape[1])
        if m.shape != rgb.shape[:2]: m = cv2.resize(m, (rgb.shape[1], rgb.shape[0]))
        m = _affiner(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255, m)
        m = np.clip((m - 0.5) * 1.6 + 0.5, 0, 1)
        if self.precedent is not None: m = 0.65 * m + 0.35 * self.precedent   # évite le scintillement
        self.precedent = m
        _, f = self.visages.detect(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        visage = None
        if f is not None and len(f):
            r = max(f, key=lambda r: r[2] * r[3] * r[-1])
            visage = (r[0] + r[2] / 2, r[1] + r[3] / 2, r[2])
        else:   # pas de visage détecté : on le devine depuis le haut du masque
            lignes = np.where((m > 0.5).sum(1) > m.shape[1] * 0.01)[0]
            if len(lignes):
                haut = lignes[0]; bande = m[haut:haut + max(4, int(m.shape[0] * 0.06))] > 0.5
                xs = np.where(bande.any(0))[0]; lw = max(8.0, (xs.max() - xs.min()) * 0.8)
                visage = (float(xs.mean()), haut + lw * 0.7, lw)
        return (m * 255).astype(np.uint8), visage


def lisser(valeurs, fps, tau=0.18):
    """Comble les trous puis lisse dans les deux sens (aucun retard)."""
    ok = [i for i, v in enumerate(valeurs) if v is not None]
    if not ok: return None
    a = np.array([v if v is not None else (np.nan,) * 3 for v in valeurs], np.float64)
    for k in range(3):
        col = a[:, k]; bon = ~np.isnan(col)
        col[~bon] = np.interp(np.where(~bon)[0], np.where(bon)[0], col[bon]); a[:, k] = col
    alpha = 1 - math.exp(-1 / (fps * tau))
    for i in range(1, len(a)): a[i] = a[i - 1] + alpha * (a[i] - a[i - 1])
    for i in range(len(a) - 2, -1, -1): a[i] = a[i + 1] + alpha * (a[i] - a[i + 1])
    return a
