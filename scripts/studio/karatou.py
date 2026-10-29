"""Famille Karatou : nos effets à nous (transitions pixel et toupie, écran partagé façon Karatou)."""
import math, os
import numpy as np
import cv2
from PIL import Image, ImageDraw
from . import effet
from .base import borne, sortie, douce, couleur, police, mot, boite, avec_ombre, composer, poser, memo, OR, NUIT, BLEU

BLANC = (255, 255, 255)


def _oui(v, defaut=False):
    if v is None: return defaut
    return str(v).lower() in ('1', 'oui', 'yes', 'true', 'vrai')


# ------------------------------------------------------------------ K1
@effet('pixelisation', 'Karatou : l\'image se casse en gros pixels puis se reforme (transition). toi=oui pour rester net pendant que le décor se pixelise',
       alias=('pixel', 'pixelate', 'pixels'))
def pixelisation(s, e):
    p = borne(s.t / e.d)
    k = math.sin(math.pi * p) ** 1.5                     # monte puis redescend, pic au milieu
    if k < .02: return
    taille = float(e.o.get('taille', e.o.get('size', 54))) * s.W / 1080
    b = max(1, int(1 + (taille - 1) * k))
    if b < 2: return
    h, w = s.img.shape[:2]
    petit = cv2.resize(s.img, (max(1, w // b), max(1, h // b)), interpolation=cv2.INTER_AREA)
    if k > .5:                                          # au pic, palette réduite façon jeu vidéo
        n = 6 + int(10 * (1 - k)); petit = np.round(petit * n) / n
    gros = cv2.resize(petit, (w, h), interpolation=cv2.INTER_NEAREST)
    if _oui(e.o.get('toi')):
        m = s.masque[..., None]; s.img = s.img * m + gros * (1 - m)
    else:
        s.img = gros
    if _oui(e.o.get('grille'), True) and b >= 8:        # fine grille sombre entre les blocs
        s.img[::b, :] *= .82; s.img[:, ::b] *= .82


# ------------------------------------------------------------------ K2
@effet('toupie', 'Karatou : l\'image tourne sur elle-même avec un flou de vitesse, puis se pose (transition). tours=1 par défaut',
       alias=('spin', 'rotation', 'tourbillon'))
def toupie(s, e):
    p = borne(s.t / e.d); tours = float(e.o.get('tours', e.o.get('turns', 1)))
    sens = -1 if str(e.o.get('sens', 'droite')).lower() in ('gauche', 'left') else 1
    q = douce(p); ang = sens * 360 * tours * q
    vit = abs(math.sin(math.pi * p))                    # vitesse (pour le flou et le recul)
    z = 1 - .28 * vit
    h, w = s.img.shape[:2]; c = (w / 2, h / 2)
    fond = cv2.GaussianBlur(cv2.resize(s.img, (w // 8, h // 8)), (0, 0), 6)
    fond = cv2.resize(fond, (w, h)) * .55
    src = s.img; acc = np.zeros_like(src); n = 1 + int(4 * vit)
    for j in range(n):                                   # flou de vitesse : plusieurs angles proches
        a = ang - sens * j * 7 * vit * tours
        M = cv2.getRotationMatrix2D(c, a, z)
        acc += cv2.warpAffine(src, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(-1, -1, -1))
    acc /= n
    trou = (acc < 0).any(axis=2, keepdims=True)
    s.img = np.where(trou, fond, np.clip(acc, 0, 1)).astype(np.float32)
    s.masque = np.zeros_like(s.masque)                  # pendant la rotation, plus de détourage fiable


# ------------------------------------------------------------------ K3
def _lecteur(chemin):
    cap = cv2.VideoCapture(chemin); fps = cap.get(cv2.CAP_PROP_FPS) or 30; n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1)
    return {'cap': cap, 'fps': fps, 'n': n, 'i': -1, 'im': None}


def _image_haut(s, e):
    src = e.o.get('haut', e.o.get('top'))
    if src and os.path.exists(str(src)):
        ext = str(src).lower().rsplit('.', 1)[-1]
        if ext in ('mp4', 'mov', 'm4v', 'webm'):
            L = memo(e, 'lecteur', lambda: _lecteur(str(src)))
            j = int(s.t * L['fps']) % max(1, L['n'])
            if j < L['i']: L['cap'].set(cv2.CAP_PROP_POS_FRAMES, j); L['i'] = j - 1
            while L['i'] < j:
                ok, im = L['cap'].read()
                if not ok: break
                L['i'] += 1; L['im'] = im
            if L['im'] is not None: return Image.fromarray(cv2.cvtColor(L['im'], cv2.COLOR_BGR2RGB))
        else:
            return memo(e, 'image', lambda: Image.open(str(src)).convert('RGB'))
    if e.cartes: return e.cartes[int(e.o.get('choix', 0)) % len(e.cartes)].convert('RGB')
    return None


@effet('ecran-partage', 'Karatou : notre écran partagé. Contenu en haut (image ou vidéo, option haut=fichier), ton visage recadré en bas, une ligne or et un titre sur la jonction',
       alias=('split', 'split-screen', 'partage'), cartes=True)
def ecran_partage(s, e):
    W, H = s.W, s.H
    hp = float(e.o.get('hauteur', .5)); HH = int(H * hp); BH = H - HH
    k = sortie(s.t / .25) if _oui(e.o.get('anime'), True) else 1.0
    k *= borne((e.d - s.t) / .2) if _oui(e.o.get('sortie'), True) else 1.0
    if k <= .01: return
    # bas : ton visage recadré pour remplir la moitié basse
    z = float(e.o.get('zoom', 1.15)); bw = int(W / z); bh = int(BH / z)
    cx = int(borne(s.vx - bw / 2, 0, W - bw)); cy = int(borne(s.vy - bh * .38, 0, H - bh))
    bas = cv2.resize(s.img[cy:cy + bh, cx:cx + bw], (W, BH), interpolation=cv2.INTER_LINEAR)
    # haut : le contenu
    im = _image_haut(s, e)
    if im is not None:
        r = max(W / im.width, HH / im.height); t = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.BILINEAR)
        g, hh = (t.width - W) // 2, int((t.height - HH) * .4)
        haut = np.asarray(t.crop((g, hh, g + W, hh + HH)), np.float32) / 255
    else:
        haut = np.ones((HH, W, 3), np.float32) * np.float32(NUIT) / 255
    sortie_img = np.concatenate([haut, bas], axis=0)
    off = int((1 - k) * HH)                               # le panneau du haut descend en entrant
    if off > 0: sortie_img[:HH] = np.concatenate([s.img[:off], haut[:HH - off]], axis=0)
    s.img = sortie_img.astype(np.float32); s.masque = np.zeros_like(s.masque)
    ep = max(4, H // 240); c = np.float32(couleur(e.o.get('couleur', e.o.get('color')), OR)) / 255
    s.img[HH - ep // 2:HH + ep // 2] = c
    txt = e.o.get('texte', e.o.get('text'))
    if txt:
        tg = memo(e, 'titre', lambda: mot(str(txt).upper(), W * .05, 'noir', NUIT))
        pw, ph = int(tg.width + W * .08), int(tg.height * 1.5)
        pil = boite(pw, ph, ph / 2, couleur(e.o.get('couleur'), OR) + (255,)); pil.alpha_composite(tg, ((pw - tg.width) // 2, (ph - tg.height) // 2))
        poser(s, avec_ombre(pil, 12, 6, 110), W / 2, HH, .7 + .3 * sortie(s.t / .3), 0, borne(s.t / .15) * borne((e.d - s.t) / .2))
