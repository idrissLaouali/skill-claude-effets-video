"""Effets de caméra et d'image : zooms, lumière, étalonnage, transitions."""
import math, random
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
from . import effet
from .base import (borne, sortie, douce, rebond, couleur, police, mot, mot_ajuste, boite, avec_ombre, pil_vers_np,
                   etalonner, composer, poser, zoom, zoom_visage, assombrir_bords, entree_sortie, memo, vide,
                   CREME, ENCRE, OR, BLEU)

_grilles = {}


def grille(s):
    if (s.W, s.H) not in _grilles:
        yy, xx = np.mgrid[0:s.H, 0:s.W].astype(np.float32); _grilles[(s.W, s.H)] = (xx, yy)
    return _grilles[(s.W, s.H)]


# ------------------------------------------------------------------ 3
@effet('verrouille', 'Des crochets se verrouillent sur ton visage et la caméra te suit', alias=('locked-on', 'cible', 'lock'))
def verrouille(s, e):
    zoom_visage(s, 1 + (float(e.o.get('zoom', 1.35)) - 1) * sortie(s.t / 0.6))
    serre = sortie(s.t / 0.22)
    r = s.vt * 0.85 * (1 + 0.6 * (1 - serre))
    a = borne(s.t / 0.12) * borne((e.d - s.t) / 0.2)
    taille = int(2 * r + 40); im = vide(taille, taille * 1.25); d = ImageDraw.Draw(im)
    g, h, dr, b = 20, 20, taille - 20, im.height - 20
    L, ep = int(r * 0.32), max(4, int(s.W / 200))
    for px, py, dx, dy in ((g, h, 1, 1), (dr, h, -1, 1), (g, b, 1, -1), (dr, b, -1, -1)):
        d.line([(px, py + dy * L), (px, py), (px + dx * L, py)], fill=(255, 255, 255, 255), width=ep, joint='curve')
    poser(s, avec_ombre(im, 6, 2, 120), s.vx, s.vy, alpha=a)
    etiquette = mot(str(e.o.get('texte', 'CIBLE VERROUILLÉE')).upper(), s.W * 0.022, 'mono', ENCRE)
    pastille = boite(etiquette.width + 12, etiquette.height, etiquette.height / 2, (255, 255, 255, 235))
    pastille.alpha_composite(etiquette, (6, 0))
    poser(s, pastille, s.vx, s.vy + r * 1.25 + pastille.height, alpha=borne((s.t - 0.15) / 0.15) * a, protege=True)


# ------------------------------------------------------------------ 5
@effet('plongee', 'Un zoom rapide sur un mot, pour appuyer une phrase', alias=('lean-in', 'punch', 'zoom-mot'))
def plongee(s, e):
    z = float(e.o.get('zoom', 1.45))
    zoom_visage(s, 1 + (z - 1) * sortie(s.t / float(e.o.get('vitesse', e.o.get('speed', 0.18)))), 0.42)


# ------------------------------------------------------------------ 42
@effet('poussee-lente', 'Une poussée cinéma lente vers ton visage, la pièce devient floue', alias=('slow-push', 'push', 'push-in'))
def poussee_lente(s, e):
    p = douce(s.t / e.d)
    zoom_visage(s, 1 + (float(e.o.get('zoom', 1.6)) - 1) * p, 0.4)
    f = s.W * float(e.o.get('flou', e.o.get('blur', 0.006))) * p
    if f > 0.6:
        flou = cv2.GaussianBlur(s.img, (0, 0), f); m = s.masque[..., None]
        s.img = s.img * m + flou * (1 - m)
    assombrir_bords(s, 0.25 * p)


# ------------------------------------------------------------------ 7
@effet('projecteur', 'Les lumières s\'éteignent, toi tu restes éclairé (look=paillettes pour la version dorée)',
       alias=('spotlight', 'lumiere'))
def projecteur(s, e):
    if e.o.get('look') in ('paillettes', 'sparkle'): return projecteur_paillettes(s, e)
    zoom_visage(s, 1 + (float(e.o.get('pousse', e.o.get('push', 1.1))) - 1) * douce(s.t / e.d))
    k = entree_sortie(s, e, 0.3, 0.25)
    xx, yy = grille(s)
    d = ((xx - s.vx) / (s.W * 0.5)) ** 2 + ((yy - (s.vy + s.H * 0.2)) / (s.H * 0.46)) ** 2
    halo = np.clip(1 - d, 0, 1) ** 1.6
    lum = (1 - k * (1 - (0.2 + 0.45 * halo))) * (1 - s.masque) + s.masque * (1 + 0.04 * k)
    s.img *= lum[..., None]
    if e.o.get('texte'):
        c = couleur(e.o.get('couleur', e.o.get('color')), OR)
        im = memo(e, 'mot', lambda: mot_ajuste(e.o['texte'], s.W * 0.9, e.o.get('police', 'italique'), fill=c, halo=(c, 26)))
        poser(s, im, s.W / 2, s.vy - s.vt * 1.1, alpha=k, derriere=True)


def etoile(taille, c=(255, 244, 222)):
    t = max(8, int(taille)); m = t / 2; f = t * 0.075
    im = vide(t, t)
    ImageDraw.Draw(im).polygon([(m, t * .02), (m + f, m - f), (t * .98, m), (m + f, m + f), (m, t * .98), (m - f, m + f), (t * .02, m), (m - f, m - f)],
                               fill=tuple(c) + (255,))
    g = im.filter(ImageFilter.GaussianBlur(t * 0.07)); out = Image.alpha_composite(g, g); out.alpha_composite(im)
    return out


def texte_degrade(txt, taille, style, haut, bas, halo=None):
    f = police(style, taille); x0, y0, x1, y1 = f.getbbox(txt); m = int(taille * 0.25 + (halo[1] * 2.5 if halo else 0))
    w, h = x1 - x0 + 2 * m, y1 - y0 + 2 * m
    masque = Image.new('L', (w, h), 0); ImageDraw.Draw(masque).text((m - x0, m - y0), txt, font=f, fill=255)
    g = np.linspace(0, 1, h)[:, None, None]; col = np.float32(haut) * (1 - g) + np.float32(bas) * g
    im = Image.fromarray(np.dstack([np.broadcast_to(col, (h, w, 3)).astype(np.uint8), np.asarray(masque)]), 'RGBA')
    if halo:
        gl = Image.new('RGBA', (w, h), tuple(halo[0]) + (0,)); gl.putalpha(masque.filter(ImageFilter.GaussianBlur(halo[1])))
        im = Image.alpha_composite(Image.alpha_composite(gl, gl), im)
    return im


def projecteur_paillettes(s, e):
    k = entree_sortie(s, e, 0.25, 0.2)
    zoom_visage(s, 1 + (float(e.o.get('pousse', 1.12)) - 1) * douce(s.t / e.d), 0.46)
    dore = np.float32(couleur(e.o.get('couleur'), (255, 190, 128))) / 255
    xx, yy = grille(s)
    d = ((xx - s.vx) / (s.W * 0.55)) ** 2 + ((yy - (s.vy + s.H * 0.15)) / (s.H * 0.5)) ** 2
    halo = np.clip(1 - d, 0, 1) ** 1.5
    s.img *= ((1 - k * (0.92 - 0.3 * halo)) * (1 - s.masque) + s.masque * (1 + 0.06 * k))[..., None]
    ox, oy, q = s.vx, s.vy - s.vt * 1.1, 4
    sy, sx = np.mgrid[0:s.H // q, 0:s.W // q].astype(np.float32) * q
    ang, ray = np.arctan2(sy - oy, sx - ox), np.hypot(sx - ox, sy - oy)
    rayons = (0.5 + 0.5 * np.cos(16 * ang + s.t * 0.9)) ** 5 * np.exp(-ray / (s.H * 0.42)) + 0.9 * np.exp(-(ray / (s.H * 0.2)) ** 2)
    rayons = cv2.resize(rayons.astype(np.float32), (s.W, s.H))
    contour = np.clip(cv2.GaussianBlur(s.masque, (0, 0), s.W * 0.012) * 1.6 - s.masque, 0, 1)
    s.img += (rayons * 0.32 + contour * 0.7)[..., None] * dore * k * (1 - s.masque[..., None])
    txt = str(e.o.get('texte', 'KARATOU'))

    def fabrique():
        t = int(s.H * 0.2)
        while t > 20 and police('italique', t).getlength(txt) > s.W * 0.86: t = int(t * 0.94)
        im = texte_degrade(txt, t, 'italique', (255, 255, 250), (255, 200, 130), halo=(tuple(int(v * 255) for v in dore), t * 0.06))
        return np.asarray(avec_ombre(im, int(t * 0.05), 0, 200), np.float32) / 255
    w = memo(e, 'mot', fabrique); wh, ww = w.shape[:2]
    reflet = np.exp(-(((np.arange(ww)[None, :] + np.arange(wh)[:, None] * 0.5) - (-0.3 + 1.6 * borne((s.t - 0.25) / 0.9)) * ww * 1.3) / (ww * 0.07)) ** 2)
    w2 = w.copy(); w2[..., :3] = np.clip(w2[..., :3] + reflet[..., None] * 0.9, 0, 1)
    poser(s, Image.fromarray((w2 * 255).astype(np.uint8), 'RGBA'), s.W / 2, max(wh * 0.5 + s.H * 0.06, s.vy - s.vt * 1.05 - wh * 0.28),
          1.08 - 0.08 * sortie(s.t / 0.5), 0, k, derriere=True)
    et = memo(e, 'etoile', lambda: etoile(s.W * 0.07))
    points = memo(e, 'points', lambda: [(r.uniform(.04, .96), r.uniform(.07, .62), r.uniform(.025, .07), r.uniform(0, 6.3), r.uniform(5, 9), r.random() < .35)
                                         for r in [random.Random(9)] for _ in range(48)])
    for x, y, t, ph, v, devant in points:
        a = max(0.0, math.sin(ph + s.t * v)) ** 2 * k
        if a > 0.03:
            poser(s, et, x * s.W, y * s.H, t / 0.07 * (0.45 + 0.75 * a), s.t * 40 + ph * 30, a, derriere=not devant, protege=devant)


# ------------------------------------------------------------------ 9
@effet('ambiance', 'Un étalonnage cinéma : plus sombre, plus doux (look=sombre, nb, chaud, froid, vif)', alias=('moody', 'grade', 'etalonnage'))
def ambiance(s, e):
    k = entree_sortie(s, e, 0.35, 0)
    s.img = s.img * (1 - k) + etalonner(s.img, e.o.get('look', e.o.get('grade', 'sombre'))) * k
    assombrir_bords(s, 0.4 * k)


# ------------------------------------------------------------------ 10
@effet('avant-apres', 'Un curseur avant / après balaie l\'image', alias=('swipe', 'avant-apres-curseur'))
def avant_apres(s, e):
    apres = etalonner(s.img, e.o.get('look', e.o.get('grade', 'sombre')))
    p = s.t / e.d
    pos = 1.05 - 0.95 * douce(p / 0.5) if p < 0.5 else 0.1 + 0.4 * douce((p - 0.5) / 0.4)
    xx, yy = grille(s)
    ligne = pos * s.W + 0.22 * (yy - s.H / 2)
    a = np.clip((xx - ligne) / 3 + 0.5, 0, 1)[..., None]
    s.img = s.img * (1 - a) + apres * a
    bord = np.clip(1 - np.abs(xx - ligne) / 3.5, 0, 1)[..., None]
    s.img = s.img * (1 - bord) + bord
    hy = s.H * 0.62; hx = pos * s.W + 0.22 * (hy - s.H / 2); r = int(s.W * 0.035)
    poignee = vide(2 * r + 4, 2 * r + 4); d = ImageDraw.Draw(poignee)
    d.ellipse([2, 2, 2 * r + 2, 2 * r + 2], fill=(255, 255, 255, 255))
    d.text((r + 2, r + 2), '‹ ›', font=police('gras', r * 0.9), fill=ENCRE + (255,), anchor='mm')
    poser(s, avec_ombre(poignee, 8, 4, 110), hx, hy)
    for lib, x in ((e.o.get('avant', 'avant'), 0.14), (e.o.get('apres', 'après'), 0.86)):
        t = mot(lib, s.W * 0.032, 'italique', ENCRE); p_ = boite(t.width + 18, t.height, t.height / 2, (255, 255, 255, 225))
        p_.alpha_composite(t, (9, 0)); poser(s, p_, s.W * x, s.H * 0.88)


# ------------------------------------------------------------------ 20
@effet('tunnel', 'L\'image s\'enfonce dans elle-même en tournant, toi tu restes devant', alias=('rabbit-hole', 'terrier'))
def tunnel(s, e):
    k = sortie(s.t / 0.4) * borne((e.d - s.t) / 0.3)
    if k <= 0: return
    pleins = np.ones((s.H, s.W), np.float32); cadre = np.zeros((s.H, s.W), np.float32); ep = max(4, s.W // 120)
    cadre[:ep] = cadre[-ep:] = 1; cadre[:, :ep] = cadre[:, -ep:] = 1
    r, z = float(e.o.get('ratio', 0.62)), (s.t * float(e.o.get('vitesse', e.o.get('speed', 0.8)))) % 1.0
    src, out = s.img, s.img.copy()
    for niv in range(1, 7):
        ech = r ** (niv - z * k)
        if ech < 0.03: break
        M = cv2.getRotationMatrix2D((s.vx, s.vy), (niv - z) * float(e.o.get('rotation', e.o.get('spin', 10))) * k, ech)
        L = cv2.warpAffine(src, M, (s.W, s.H)); a = cv2.warpAffine(pleins, M, (s.W, s.H))[..., None] * k
        b = cv2.warpAffine(cadre, M, (s.W, s.H))[..., None] * k
        out = out * (1 - a) + L * a; out = out * (1 - b) + b
    m = s.masque[..., None] * k
    s.img = out * (1 - m) + src * m


# ------------------------------------------------------------------ 34
@effet('points', 'L\'image se construit en points lumineux, puis devient nette', alias=('dot-reveal', 'pixels'))
def points(s, e):
    p = borne(s.t / e.d); W, H = s.W, s.H
    c = max(6, int(W * float(e.o.get('cellule', e.o.get('cell', 0.017))))); gh, gw = H // c + 1, W // c + 1

    def geo():
        yy, xx = np.mgrid[0:gh * c, 0:gw * c].astype(np.float32)
        dist = np.sqrt((xx % c - c / 2 + 0.5) ** 2 + (yy % c - c / 2 + 0.5) ** 2)[:H, :W]
        return dist, np.random.default_rng(5).random((gh, gw)).astype(np.float32)
    dist, seuil = memo(e, 'geo', geo)
    pad = np.pad(s.img, ((0, gh * c - H), (0, gw * c - W), (0, 0)), mode='edge')
    petit = cv2.resize(pad, (gw, gh), interpolation=cv2.INTER_AREA)
    lum = petit @ np.float32([0.299, 0.587, 0.114])
    allume = np.clip((p * 1.7 - seuil * 0.95) / 0.3, 0, 1)
    scint = 0.75 + 0.25 * np.sin(seuil * 40 + s.t * 18)
    r = (0.18 + 0.32 * np.sqrt(np.clip(lum, 0, 1))) * c * allume
    col = couleur(e.o.get('couleur', e.o.get('color')), OR); q2 = borne((p - 0.3) / 0.35)
    dc = np.float32(col) / 255 * (0.55 + 0.6 * lum[..., None]) * scint[..., None] * (1 - q2) + np.clip(petit * 1.15, 0, 1) * q2
    R = np.repeat(np.repeat(r, c, 0), c, 1)[:H, :W]; DC = np.repeat(np.repeat(dc, c, 0), c, 1)[:H, :W]
    dm = np.clip(R - dist + 0.5, 0, 1)[..., None]
    fond = np.float32(couleur(e.o.get('fond'), (10, 14, 24))) / 255
    q = douce((p - 0.6) / 0.4)
    s.img = (fond * (1 - dm) + DC * dm) * (1 - q) + s.img * q


# ------------------------------------------------------------------ 14
def trace(d, pts, c, ep, frac):
    n = max(2, int(len(pts) * borne(frac)))
    if frac > 0: d.line(pts[:n], fill=c, width=ep, joint='curve')


def courbe(x0, y0, x1, y1, courbure=0.25, n=40):
    mx, my = (x0 + x1) / 2 - (y1 - y0) * courbure, (y0 + y1) / 2 + (x1 - x0) * courbure
    return [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t * t * y1)
            for t in np.linspace(0, 1, n)]


def pointe(d, pts, c, ep, taille):
    (xa, ya), (xb, yb) = pts[-4], pts[-1]; a = math.atan2(yb - ya, xb - xa)
    for k in (2.6, -2.6): d.line([(xb, yb), (xb + taille * math.cos(a + k), yb + taille * math.sin(a + k))], fill=c, width=ep)


@effet('pause-fleche', 'Arrêt sur image, une flèche dessinée à la main pointe vers toi', alias=('pause-point', 'pause', 'arret'))
def pause_fleche(s, e):
    if 'fige' not in e.memo: e.memo['fige'] = (s.img.copy(), s.masque.copy(), s.vx, s.vy, s.vt)
    img, m, s.vx, s.vy, s.vt = e.memo['fige']; s.img, s.masque = img.copy(), m
    zoom_visage(s, 1 + 0.06 * sortie(s.t / e.d), 0.4)
    s.img = s.img * 0.92 + etalonner(s.img, 'nb') * 0.08
    c = couleur(e.o.get('couleur', e.o.get('color')), OR) + (255,)
    calque = vide(s.W, s.H); d = ImageDraw.Draw(calque)
    d.rounded_rectangle([s.W * .05, s.H * .06, s.W * .15, s.H * .06 + s.W * .1], 16, fill=(0, 0, 0, 150))
    for bx in (0.075, 0.11): d.rectangle([s.W * bx, s.H * .06 + s.W * .025, s.W * (bx + .017), s.H * .06 + s.W * .075], fill=(255, 255, 255, 230))
    tx, ty = s.W * float(e.o.get('x_texte', e.o.get('label_x', 0.72))), s.vy - s.vt * 2.2
    pts = courbe(tx - s.W * 0.05, ty + s.W * 0.06, s.vx + s.vt * 0.75, s.vy - s.vt * 0.35, 0.3)
    k = sortie((s.t - 0.15) / 0.4); ep = max(6, s.W // 140)
    trace(d, pts, c, ep, k)
    if k >= 0.99: pointe(d, pts, c, ep, s.W * 0.04)
    composer(s, calque, 0, 0)
    lib = mot(e.o.get('texte', 'regarde ici'), s.W * 0.07, 'feutre', c[:3], ombre=6)
    poser(s, lib, tx, ty - lib.height * 0.2, 0.7 + 0.3 * rebond(s.t / 0.3), -6, borne(s.t / 0.1), protege=True)


# ------------------------------------------------------------------ 15
@effet('desinstallation', 'Une barre de désinstallation glitchée qui casse l\'image', alias=('uninstall', 'glitch'))
def desinstallation(s, e):
    p = borne(s.t / e.d); g = p ** 1.6; rnd = np.random.default_rng(int(s.temps * 30))
    dec = int(g * s.W * 0.025)
    if dec: s.img = np.stack([np.roll(s.img[..., 0], dec, 1), s.img[..., 1], np.roll(s.img[..., 2], -dec, 1)], -1)
    for _ in range(int(2 + g * 10)):
        y0, hh = int(rnd.uniform(0, s.H)), int(rnd.uniform(8, 60))
        s.img[y0:y0 + hh] = np.roll(s.img[y0:y0 + hh], int(rnd.uniform(-1, 1) * g * s.W * 0.08), 1)
    if p > 0.82:
        q = (p - 0.82) / 0.18; f = 1 + int(q * 40)
        petit = cv2.resize(s.img, (max(1, s.W // f), max(1, s.H // f)), interpolation=cv2.INTER_AREA)
        s.img = cv2.resize(petit, (s.W, s.H), interpolation=cv2.INTER_NEAREST) * (1 - 0.6 * q)
    bw, bh = int(s.W * 0.7), int(s.W * 0.2)
    im = boite(bw, bh, 22, (245, 245, 247, 240)); d = ImageDraw.Draw(im)
    d.text((bw * .06, bh * .28), e.o.get('texte', 'Désinstallation...'), font=police('ui', bh * .18), fill=ENCRE + (255,), anchor='lm')
    d.rounded_rectangle([bw * .06, bh * .56, bw * .94, bh * .7], 8, fill=(215, 215, 220, 255))
    d.rounded_rectangle([bw * .06, bh * .56, bw * .06 + bw * .88 * max(.03, douce(p)), bh * .7], 8, fill=BLEU + (255,))
    d.text((bw * .94, bh * .85), f'{int(douce(p) * 100)} %', font=police('ui', bh * .13), fill=(110, 110, 110, 255), anchor='rm')
    poser(s, avec_ombre(im, 16, 8, 120), s.W / 2, s.H * 0.16, 0.8 + 0.2 * rebond(s.t / 0.3), 0, borne(s.t / 0.1))


# ------------------------------------------------------------------ 16
def coeur(taille, c=(255, 48, 64)):
    t = int(taille); im = vide(t, t)
    pts = [(t / 2 + t * .48 * (16 * math.sin(a) ** 3) / 16,
            t * .46 - t * .46 * (13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)) / 16)
           for a in np.linspace(0, 2 * math.pi, 60)]
    ImageDraw.Draw(im).polygon(pts, fill=tuple(c) + (255,)); return im


def icones_reel(taille):
    t = int(taille); im = vide(t, t * 3.6); d = ImageDraw.Draw(im); ep = max(3, t // 12)
    im.alpha_composite(coeur(t * 0.8, (255, 255, 255)), (int(t * 0.1), 0))
    d.text((t / 2, t * .95), '26,9 k', font=police('ui', t * .24), fill=(255, 255, 255, 255), anchor='mm')
    d.ellipse([t * .15, t * 1.25, t * .85, t * 1.95], outline=(255, 255, 255, 255), width=ep)
    d.text((t / 2, t * 2.15), '412', font=police('ui', t * .24), fill=(255, 255, 255, 255), anchor='mm')
    d.polygon([(t * .12, t * 2.75), (t * .9, t * 2.45), (t * .55, t * 3.25), (t * .45, t * 2.88)], outline=(255, 255, 255, 255), width=ep)
    return im


@effet('cadre-reel', 'Ta vidéo rétrécit dans une carte de reel Instagram', alias=('reel-frame', 'reel'))
def cadre_reel(s, e):
    k = sortie(s.t / 0.35) * borne((e.d - s.t) / 0.3)
    if k <= 0: return
    ech = 1 - 0.2 * k
    petit = cv2.resize(s.img, (s.W // 16, s.H // 16), interpolation=cv2.INTER_AREA)
    fond = cv2.GaussianBlur(cv2.resize(petit, (s.W, s.H)), (0, 0), 12) * (1 - 0.45 * k)
    iw, ih = int(s.W * ech), int(s.H * ech)
    encart = cv2.resize(s.img, (iw, ih), interpolation=cv2.INTER_AREA)
    m = pil_vers_np(boite(iw, ih, s.W * 0.05 * k + 1, (255, 255, 255, 255)))[..., 3:4]
    x0, y0 = (s.W - iw) // 2, int((s.H - ih) * 0.42)
    zone = fond[y0:y0 + ih, x0:x0 + iw]; zone[:] = zone * (1 - m) + encart * m; s.img = fond
    mm = np.zeros_like(s.masque); mm[y0:y0 + ih, x0:x0 + iw] = cv2.resize(s.masque, (iw, ih)); s.masque = mm
    s.vx, s.vy, s.vt = x0 + s.vx * ech, y0 + s.vy * ech, s.vt * ech
    ic = memo(e, 'icones', lambda: avec_ombre(icones_reel(s.W * 0.075), 6, 2, 120))
    composer(s, ic, x0 + iw - ic.width - s.W * 0.01, y0 + ih * 0.52, k)
    nom = mot(e.o.get('texte', '@idrisstechinsider'), s.W * 0.032, 'ui', (255, 255, 255), ombre=4)
    composer(s, nom, x0 + s.W * 0.03, y0 + ih - nom.height - s.W * 0.04, k)
