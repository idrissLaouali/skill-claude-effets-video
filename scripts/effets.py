#!/usr/bin/env python3
"""Effets vidéo pour Claude, par Idriss Laouali (Karatou Academy).

Un effet :       python effets.py orbite entree.mp4 sortie.mp4 --debut 3.2 --fin 6
Plusieurs :      python effets.py --plan plan.json entree.mp4 sortie.mp4
Vérification :   python effets.py --plan plan.json entree.mp4 verif.png --apercu 4.5,9
La liste :       python effets.py --liste
"""
import argparse, json, os, subprocess, sys
import numpy as np
import cv2
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from studio import EFFETS, Effet, AVEC_CARTES, charger_tout, resoudre  # noqa: E402
from studio.base import Scene  # noqa: E402
from studio.suivi import infos, images, Suivi, lisser  # noqa: E402

CLES = {'fx': 'effet', 'start': 'debut', 'end': 'fin', 'text': 'texte'}


def normaliser(d):
    """Accepte les clés françaises (effet, debut, fin, texte) ou anglaises (fx, start, end, text)."""
    return {CLES.get(k, k): v for k, v in d.items()}


def vignettes(dossier, auto):
    out = []
    if dossier and os.path.isdir(dossier):
        for n in sorted(os.listdir(dossier)):
            p = os.path.join(dossier, n); ext = n.lower().rsplit('.', 1)[-1]
            if ext in ('jpg', 'jpeg', 'png', 'webp'): out.append(Image.open(p).convert('RGB'))
            elif ext in ('mp4', 'mov', 'm4v', 'webm'):
                cap = cv2.VideoCapture(p); cap.set(cv2.CAP_PROP_POS_MSEC, 1000); ok, im = cap.read(); cap.release()
                if ok: out.append(Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)))
    return out or auto


def main():
    charger_tout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('args', nargs='*', help='[effet] entree.mp4 sortie.mp4')
    ap.add_argument('--plan'); ap.add_argument('--debut', type=float); ap.add_argument('--fin', type=float)
    ap.add_argument('--texte'); ap.add_argument('--images'); ap.add_argument('--opt', action='append', default=[], help='cle=valeur')
    ap.add_argument('--apercu', help='secondes séparées par des virgules : enregistre des PNG au lieu de la vidéo')
    ap.add_argument('--largeur', type=int, default=1080, help='petit côté de la sortie (1080 par défaut, 2160 pour la 4K)')
    ap.add_argument('--liste', action='store_true')
    ap.add_argument('--son', action='store_true', help='ajoute la bande son Karatou (drops, suspense, bruitages) sous ta voix')
    ap.add_argument('--hook', type=float, help='avec --son : seconde du drop d\'ouverture (suspense avant)')
    a = ap.parse_args()
    if a.liste:
        for i, (k, (_, d)) in enumerate(EFFETS.items()): print(f'{i + 1:2d}. {k:22s} {d}')
        return
    if a.plan:
        src, dst = a.args[0], a.args[1]
        brut = json.load(open(a.plan)); plan = brut.get('effets', brut.get('effects', brut)) if isinstance(brut, dict) else brut
        if isinstance(brut, dict):
            a.son = a.son or bool(brut.get('son', brut.get('sound', False)))
            if a.hook is None and brut.get('hook') is not None: a.hook = float(brut['hook'])
        plan = [normaliser(d) for d in plan]
    else:
        nom, src, dst = a.args[0], a.args[1], a.args[2]
        d = {'effet': nom, 'debut': a.debut or 0.0, 'fin': a.fin if a.fin is not None else 1e9}
        if a.texte: d['texte'] = a.texte
        if a.images: d['images'] = a.images
        for kv in a.opt: k, v = kv.split('=', 1); d[k] = v
        plan = [d]
    for d in plan:
        if resoudre(d['effet']) not in EFFETS: sys.exit(f"Effet inconnu : '{d['effet']}'. Lance --liste pour voir les {len(EFFETS)} effets.")

    fps, duree, sw, sh = infos(src)
    for d in plan: d['fin'] = min(float(d.get('fin', 1e9)), duree)
    if sw <= sh: W = a.largeur; H = int(round(a.largeur * sh / sw / 2)) * 2
    else: H = a.largeur; W = int(round(a.largeur * sw / sh / 2)) * 2
    aw = 540 if sw <= sh else int(round(540 * sw / sh / 2)) * 2
    ah = int(round(aw * sh / sw / 2)) * 2
    fx = [Effet(d) for d in plan]
    utile = lambda t: any(f.debut - 0.5 <= t < f.fin + 0.5 for f in fx)

    print(f'Étape 1 : je te repère dans la vidéo ({len(fx)} effet{"s" * (len(fx) > 1)})...', flush=True)
    suivi = Suivi(aw, ah); masques, visages, auto = {}, [], []
    prises = {int(duree * fps * (j + 0.5) / 10) for j in range(10)}
    for i, im in enumerate(images(src, aw, ah, fps)):
        t = i / fps
        if i in prises: auto.append(Image.fromarray(im.copy()))
        if utile(t):
            m, v = suivi(im, int(t * 1000)); masques[i] = m; visages.append(v)
        else:
            visages.append(None); suivi.oublier()
    lisse = lisser(visages, fps)
    if lisse is None: lisse = np.tile([aw / 2, ah * 0.33, aw * 0.15], (len(visages), 1))
    for f in fx:
        if f.nom in AVEC_CARTES: f.cartes = vignettes(f.o.get('images'), auto)

    apercus = sorted({int(round(float(x) * fps)) for x in a.apercu.split(',')}) if a.apercu else None
    enc = None
    if not apercus:
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
                                '-i', src, '-map', '0:v', '-map', '1:a:0?', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium',
                                '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', dst],
                               stdin=subprocess.PIPE)
    print('Étape 2 : j\'ajoute les effets...', flush=True)
    k = W / aw
    for i, im in enumerate(images(src, W, H, fps)):
        t = i / fps
        if apercus is not None and i not in apercus:
            if i > apercus[-1]: break
            continue
        actifs = [f for f in fx if f.debut <= t < f.fin]
        if actifs:
            s = Scene(); s.W, s.H, s.temps, s.fps, s.u = W, H, t, fps, W / 1080
            s.img = im.astype(np.float32) / 255.0
            m = masques.get(i)
            s.masque = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0 if m is not None else np.zeros((H, W), np.float32)
            vx, vy, vt = lisse[min(i, len(lisse) - 1)]
            s.vx, s.vy, s.vt = vx * k, vy * k, max(vt * k, W * 0.05)
            for f in actifs:
                s.t = t - f.debut
                EFFETS[f.nom][0](s, f)
            im = (np.clip(s.img, 0, 1) * 255 + 0.5).astype(np.uint8)
        if apercus is not None:
            out = dst if len(apercus) == 1 else dst.replace('.png', f'_{t:.2f}.png')
            cv2.imwrite(out, cv2.cvtColor(im, cv2.COLOR_RGB2BGR)); print('enregistré', out)
        else:
            enc.stdin.write(im.tobytes())
            if i % int(fps * 5) == 0: print(f'  {t:5.1f} s / {duree:.1f} s', flush=True)
    if enc:
        enc.stdin.close(); enc.wait()
        if a.son:
            from studio import son
            print('Étape 3 : la bande son...', flush=True)
            piste = son.bande_son([{'nom': f.nom, 'debut': f.debut, 'fin': f.fin} for f in fx], duree, son.lire_audio(src, duree), a.hook)
            tmp_wav, tmp_mp4 = dst + '.son.wav', dst + '.tmp.mp4'
            son.ecrire_wav(tmp_wav, piste)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', dst, '-i', tmp_wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac',
                            '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp_mp4], check=True)
            os.replace(tmp_mp4, dst); os.remove(tmp_wav)
        print('Terminé :', dst)
    suivi.decoupe.close()


if __name__ == '__main__':
    main()
