"""Le verre : cartes en verre liquide (réfraction, reflet, frange de couleur) et les effets qui en sont faits."""
import math, re
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
from . import effet
from .base import (borne, sortie, douce, rebond, couleur, police, mot, boite, avec_ombre, etalonner, composer, poser,
                   zoom, zoom_visage, entree_sortie, apparait, memo, vide, personne_devant, CLAUDE, VERT, OR, BLEU, ROUGE)

BLANC = (255, 255, 255)


# ------------------------------------------------------------------ fabrication du verre
def _champ_distance(w, h, r):
    """Distance signée à un rectangle arrondi (négative à l'intérieur) et la normale vers le bord."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    q = np.stack([np.abs(xx - w / 2) - (w / 2 - r), np.abs(yy - h / 2) - (h / 2 - r)], -1)
    sdf = np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(np.maximum(q[..., 0], q[..., 1]), 0) - r
    nx, ny = xx - w / 2, yy - h / 2; n = np.sqrt(nx * nx + ny * ny) + 1e-3
    return xx, yy, sdf, nx / n, ny / n


def verre(s, w, h, r, cx, cy, teinte=(255, 255, 255), dose=0.2, sombre=0.0, flou=None, opacite=255):
    """Renvoie une image RGBA en verre liquide fabriquée à partir de ce qui se trouve derrière (cx, cy)."""
    w, h, r = int(w), int(h), max(2.0, float(r)); u = s.W / 2160
    x0, y0, m = int(cx - w / 2), int(cy - h / 2), int(140 * u) + 4
    xs = np.clip(np.arange(x0 - m, x0 + w + m), 0, s.W - 1); ys = np.clip(np.arange(y0 - m, y0 + h + m), 0, s.H - 1)
    fond = cv2.GaussianBlur(np.ascontiguousarray(s.img[np.ix_(ys, xs)]), (0, 0), max(3.0, (flou or s.W / 40) * 0.3))
    xx, yy, sdf, nx, ny = _champ_distance(w, h, r)
    d = np.maximum(-sdf, 0) / u
    k = (70 * np.exp(-d / 14) + 34 * np.exp(-d / 70) + 10 * np.exp(-d / 260)) * u   # la lumière se courbe au bord
    out = np.zeros((h, w, 3), np.float32)
    for c, f in enumerate((1.10, 1.0, 0.90)):                                          # frange rouge / bleue
        out[..., c] = cv2.remap(fond[..., c], (xx + m + nx * k * f).astype(np.float32), (yy + m + ny * k * f).astype(np.float32),
                                cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    out = out * (1 - sombre * 0.3) * 0.9 + np.float32(teinte) / 255 * dose * 0.25 + 0.05 * (1 - 0.3 * yy / h)[..., None] - 0.04
    out = out * (1 - sombre * 0.55)
    reflet = np.exp(-d / 5) * np.clip(0.55 - 0.45 * (nx * 0.6 + ny * 0.8), 0, 1)       # lumière venant d'en haut à gauche
    out = np.clip(out + (reflet * 0.85 + np.exp(-d / 30) * 0.10)[..., None], 0, 1)
    a = (np.clip(0.5 - sdf, 0, 1) * opacite).astype(np.uint8)
    im = Image.fromarray((out * 255).astype(np.uint8)).convert('RGBA'); im.putalpha(Image.fromarray(a))
    return im


def pastille_visage(s, e, taille):
    """Un rond découpé dans ton propre visage (pris une fois au début de l'effet)."""
    def prendre():
        r = s.vt * 0.9; x0, y0 = int(max(0, s.vx - r)), int(max(0, s.vy - r * 1.05))
        return Image.fromarray((np.clip(s.img[y0:int(y0 + 2 * r), x0:int(x0 + 2 * r)], 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    im = memo(e, 'visage', prendre).resize((int(taille), int(taille)), Image.LANCZOS)
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).ellipse([0, 0, im.width - 1, im.height - 1], fill=255); im.putalpha(m)
    return im


def coche(d, x, y, t, c=(255, 255, 255, 255), ep=None):
    d.line([(x, y + t * .5), (x + t * .36, y + t * .85), (x + t, y + t * .1)], fill=c, width=ep or max(3, int(t / 5)), joint='curve')


def nombre(txt):
    """'197K' -> (197.0, 'K', 0) ; '59 %' -> (59.0, ' %', 0) ; '4,8' -> (4.8, '', 1)."""
    m = re.match(r'\s*([\d.,]+)(.*)', str(txt))
    if not m: return 0.0, str(txt), 0
    n = m.group(1).replace(',', '.') if m.group(1).count(',') == 1 and '.' not in m.group(1) else m.group(1).replace(',', '')
    return float(n or 0), m.group(2), (len(n.split('.')[1]) if '.' in n else 0)


def compter(txt, p):
    v, suf, dec = nombre(txt)
    s = f'{v * p:.{dec}f}'.replace('.', ',')
    return s + suf


# ------------------------------------------------------------------ 23
@effet('widgets-verre', 'Des widgets en verre et des mini-pages flottent autour de ta tête, avec « Monté par Claude »',
       alias=('glass-widgets', 'glass', 'widgets'))
def widgets_verre(s, e):
    W, H = s.W, s.H; u = W / 1080
    k0 = entree_sortie(s, e, 0.3, 0)
    if e.o.get('look', 'chaud') != 'aucun': s.img = s.img * (1 - 0.6 * k0) + etalonner(s.img, e.o.get('look', 'chaud')) * 0.6 * k0
    al = borne((e.d - s.t) / 0.2); sb = float(e.o.get('sombre', 0.2))
    flotte = lambda i: 6 * u * math.sin(2 * math.pi * (s.t * 0.55 + i * 0.17))
    V = lambda w, h, cx, cy, r=None: verre(s, w, h, r or min(w, h) * 0.2, cx, cy, dose=0.14, sombre=sb)

    def montrer(im, x, y, i, devant=False):
        t0 = 0.07 * i
        if s.t >= t0:
            poser(s, im, x, y + flotte(i), 0.6 + 0.4 * apparait(s, t0, 0.32), 0, al * borne((s.t - t0) / 0.08), derriere=not devant, protege=devant)
    # 1 · le chiffre
    T = 300 * u; ax, ay = 50 * u + T / 2, 118 * u + T / 2
    a = V(T, T, ax, ay); d = ImageDraw.Draw(a)
    d.ellipse([T * .1, T * .115, T * .16, T * .175], fill=CLAUDE + (255,))
    d.text((T * .2, T * .145), e.o.get('titre', 'Claude'), font=police('ui', T * .085), fill=BLANC + (235,), anchor='lm')
    d.text((T * .08, T * .2), str(e.o.get('texte', '45')), font=police('ui-gras', T * .44), fill=BLANC + (255,))
    for j, l in enumerate(str(e.o.get('sous', 'effets|un seul clip')).split('|')):
        d.text((T * .1, T * (.7 + .11 * j)), l, font=police('ui', T * .085), fill=BLANC + (235,))
    montrer(a, ax, ay, 0)
    # 2 · la barre de rendu
    bw, bh = 400 * u, 150 * u; bx, by = W - 50 * u - bw / 2, 118 * u + bh / 2
    b = V(bw, bh, bx, by, bh * .28); d = ImageDraw.Draw(b); p = douce(s.t / max(0.3, e.d * 0.85))
    d.ellipse([bh * .17, bh * .2, bh * .28, bh * .31], fill=(255, 69, 58, 255))
    d.text((bh * .36, bh * .255), 'Rendu en cours', font=police('ui', bh * .19), fill=BLANC + (240,), anchor='lm')
    d.rounded_rectangle([bh * .17, bh * .5, bw - bh * .17, bh * .6], bh * .05, fill=BLANC + (70,))
    d.rounded_rectangle([bh * .17, bh * .5, bh * .17 + (bw - bh * .34) * max(.04, p), bh * .6], bh * .05, fill=BLANC + (245,))
    d.text((bh * .17, bh * .78), f'Rendu 4K  ·  {int(p * 100)} %', font=police('ui', bh * .14), fill=BLANC + (210,), anchor='lm')
    montrer(b, bx, by, 1)
    # 3 · le profil
    cy3 = by + bh + 22 * u
    g = V(bw, bh, bx, cy3, bh * .28); d = ImageDraw.Draw(g)
    av = pastille_visage(s, e, bh * .62); g.alpha_composite(av, (int(bw - bh * .19 - av.width), int((bh - av.height) / 2)))
    d.text((bh * .2, bh * .36), e.o.get('nom', 'Idriss'), font=police('ui-gras', bh * .22), fill=BLANC + (255,), anchor='lm')
    d.text((bh * .2, bh * .66), e.o.get('compte', '@idrisstechinsider'), font=police('ui', bh * .14), fill=BLANC + (215,), anchor='lm')
    montrer(g, bx, cy3, 2)
    # 4 · une mini-page « vues » dans le verre
    aw = ah = 330 * u; dx, dy = 50 * u + aw / 2, ay + T / 2 + 26 * u + ah / 2
    art = V(aw, ah, dx, dy, 44 * u); d = ImageDraw.Draw(art)
    d.text((24 * u, 30 * u), 'page · vues.html', font=police('mono', 15 * u), fill=BLANC + (220,), anchor='lm')
    inn = boite(aw - 36 * u, ah - 74 * u, 20 * u, (250, 248, 244, 255)); di = ImageDraw.Draw(inn); iw, ih = inn.size
    for j, c in enumerate(((255, 95, 87), (255, 189, 46), (40, 200, 64))): di.ellipse([14 * u + j * 16 * u, 14 * u, 24 * u + j * 16 * u, 24 * u], fill=c + (255,))
    di.text((16 * u, 40 * u), 'Meilleurs reels', font=police('gras', 25 * u), fill=(24, 22, 26, 255))
    di.text((16 * u, 72 * u), e.o.get('vues', '161K'), font=police('titre', 44 * u), fill=BLEU + (255,))
    vals = [161, 120, 97, 70, 52, 41, 30]; gx0, gx1, gy1 = 16 * u, iw - 16 * u, ih - 18 * u; lb = (gx1 - gx0) / 7 * .66
    for j, v in enumerate(vals):
        h_ = ih * .42 * v / vals[0] * sortie((s.t - .35 - .05 * j) / .4); x0 = gx0 + (gx1 - gx0) * j / 7
        if h_ > 1: di.rounded_rectangle([x0, gy1 - h_, x0 + lb, gy1], 5 * u, fill=(OR if j == 0 else BLEU) + (255,))
    art.alpha_composite(inn, (int(18 * u), int(56 * u)))
    montrer(art, dx, dy, 3)
    # 5 · en cours de montage
    mw, mh = 360 * u, 220 * u; mx, my = W - 50 * u - mw / 2, cy3 + bh / 2 + 22 * u + mh / 2
    mu = V(mw, mh, mx, my, 40 * u); d = ImageDraw.Draw(mu); A = int(96 * u)
    deg = np.linspace(0, 1, A, dtype=np.float32)[:, None, None]
    poch = np.concatenate([(np.float32(OR) * (1 - deg) + np.float32(CLAUDE) * deg) * np.ones((1, A, 1), np.float32), np.full((A, A, 1), 255, np.float32)], 2)
    poch = Image.fromarray(poch.astype(np.uint8), 'RGBA'); pm = Image.new('L', poch.size, 0)
    ImageDraw.Draw(pm).rounded_rectangle([0, 0, A - 1, A - 1], 16 * u, fill=255); poch.putalpha(pm)
    pd = ImageDraw.Draw(poch)
    for k in range(6):
        an = k * math.pi / 3
        pd.line([(A / 2 - 26 * u * math.cos(an), A / 2 - 26 * u * math.sin(an)), (A / 2 + 26 * u * math.cos(an), A / 2 + 26 * u * math.sin(an))], fill=BLANC + (255,), width=int(7 * u))
    mu.alpha_composite(poch, (int(22 * u), int(22 * u)))
    d.text((134 * u, 44 * u), 'MONTAGE EN COURS', font=police('mono', 14 * u), fill=BLANC + (200,), anchor='lm')
    d.text((134 * u, 78 * u), e.o.get('piste', 'sons doux'), font=police('ui-gras', 28 * u), fill=BLANC + (255,), anchor='lm')
    d.text((134 * u, 108 * u), 'effets · 25,7 s', font=police('ui', 20 * u), fill=BLANC + (200,), anchor='lm')
    pp = borne(s.t / max(0.5, e.d))
    d.rounded_rectangle([22 * u, 140 * u, mw - 22 * u, 146 * u], 3 * u, fill=BLANC + (70,))
    d.rounded_rectangle([22 * u, 140 * u, 22 * u + (mw - 44 * u) * pp, 146 * u], 3 * u, fill=BLANC + (240,))
    cxm, cym = mw / 2, 184 * u
    d.polygon([(cxm - 12 * u, cym - 16 * u), (cxm - 12 * u, cym + 16 * u), (cxm + 16 * u, cym)], fill=BLANC + (255,))
    for sg in (-1, 1):
        x = cxm + sg * 80 * u
        for o in (-10, 4):
            d.polygon([(x + sg * o * u, cym - 11 * u), (x + sg * o * u, cym + 11 * u), (x + sg * (o + 16) * u, cym)], fill=BLANC + (220,))
    montrer(mu, mx, my, 4)
    # 6 · l'agenda
    kw, kh = 330 * u, 190 * u; kx, ky = 50 * u + kw / 2, dy + ah / 2 + 26 * u + kh / 2
    ca = V(kw, kh, kx, ky, 40 * u); d = ImageDraw.Draw(ca)
    d.text((26 * u, 36 * u), e.o.get('jour', 'DIM.'), font=police('ui-gras', 22 * u), fill=(255, 92, 82, 255), anchor='lm')
    d.text((26 * u, 82 * u), str(e.o.get('date', '25')), font=police('ui-gras', 56 * u), fill=BLANC + (255,), anchor='lm')
    d.rounded_rectangle([22 * u, 120 * u, kw - 22 * u, 168 * u], 12 * u, fill=(255, 92, 82, 210))
    d.text((36 * u, 144 * u), e.o.get('evenement', 'Publier 2 reels · ce soir'), font=police('ui-gras', 21 * u), fill=BLANC + (255,), anchor='lm')
    montrer(ca, kx, ky, 5)
    # 7 · l'anneau 4K
    R = 250 * u; rx, ry = W - 50 * u - R / 2, my + mh / 2 + 26 * u + R / 2
    rg = V(R, R, rx, ry, 56 * u); d = ImageDraw.Draw(rg); rp = douce((s.t - 0.4) / 1.0); rr = R * .34
    d.ellipse([R / 2 - rr, R / 2 - rr - 8 * u, R / 2 + rr, R / 2 + rr - 8 * u], outline=BLANC + (60,), width=int(16 * u))
    if rp > 0: d.arc([R / 2 - rr, R / 2 - rr - 8 * u, R / 2 + rr, R / 2 + rr - 8 * u], -90, -90 + 360 * rp, fill=VERT + (255,), width=int(16 * u))
    d.text((R / 2, R / 2 - 8 * u), '4K', font=police('ui-gras', 52 * u), fill=BLANC + (255,), anchor='mm')
    d.text((R / 2, R - 26 * u), 'rendu', font=police('ui', 20 * u), fill=BLANC + (210,), anchor='mm')
    montrer(rg, rx, ry, 6)
    # 8 · « Monté par Claude », devant toi
    debut, fin = (str(e.o.get('pastille', 'Monté par |Claude')).split('|') + [''])[:2]
    f1, f2 = police('ui', W * .045), police('ui-gras', W * .045)
    tw = f1.getlength(debut) + f2.getlength(fin); ph = W * .105; pw = tw + ph * .9; py = H * .875
    q = verre(s, pw, ph, ph / 2, W / 2, py, teinte=(70, 70, 76), dose=0.16); d = ImageDraw.Draw(q)
    d.text(((pw - tw) / 2, ph / 2), debut, font=f1, fill=BLANC + (255,), anchor='lm')
    d.text(((pw - tw) / 2 + f1.getlength(debut), ph / 2), fin, font=f2, fill=(255, 176, 146, 255), anchor='lm')
    montrer(avec_ombre(q, 14, 6, 70), W / 2, py, 7, devant=True)


# ------------------------------------------------------------------ 37 (+ look=bento)
def _courbe_graph(lay, d, pts, y_bas, c, ep):
    if len(pts) < 2: return
    zone = vide(*lay.size); ImageDraw.Draw(zone).polygon(pts + [(pts[-1][0], y_bas), (pts[0][0], y_bas)], fill=c + (58,)); lay.alpha_composite(zone)
    lum = vide(*lay.size); ImageDraw.Draw(lum).line(pts, fill=c + (255,), width=ep * 3, joint='curve')
    lay.alpha_composite(lum.filter(ImageFilter.GaussianBlur(ep * 2)))
    ImageDraw.Draw(lay).line(pts, fill=c + (255,), width=ep, joint='curve')
    hx, hy = pts[-1]; r = ep * 1.9
    ImageDraw.Draw(lay).ellipse([hx - r, hy - r, hx + r, hy + r], fill=(255, 255, 255, 255), outline=c + (255,), width=max(2, ep // 2))


@effet('graphique-verre', 'Une carte en verre liquide sous ton menton : la courbe monte et le chiffre défile (look=bento pour la version tableau de bord)',
       alias=('liquid-glass-graph', 'liquid-glass', 'glass-graph', 'graphique'))
def graphique_verre(s, e):
    if e.o.get('look') == 'bento': return bento(s, e)
    q = sortie(s.t / 0.4); al = borne((e.d - s.t) / 0.2) * borne(s.t / 0.12)
    if al <= 0: return
    W = s.W; ech = 0.88 + 0.12 * q; gw, gh = int(W * .74 * ech), int(W * .46 * ech)
    cx, cy = W / 2, min(s.H - W * .46 * .62, s.vy + s.vt * 2.7) + (1 - q) * W * .08
    im = verre(s, gw, gh, gh * .12, cx, cy, dose=0.16, sombre=0.12, flou=W / 30)
    lay = vide(gw, gh); d = ImageDraw.Draw(lay); m = gw * .07
    g = douce((s.t - 0.25) / max(0.3, e.d * 0.72))
    d.text((m, m * .9), str(e.o.get('texte', 'RÉTENTION')).upper(), font=police('mono', gw * .04), fill=(255, 255, 255, 190))
    a, _, _ = nombre(e.o.get('de', e.o.get('from', '0'))); b, suf, dec = nombre(e.o.get('a', e.o.get('to', '59 %')))
    val = f'{a + (b - a) * g:.{dec}f}'.replace('.', ',') + suf
    f = police('ui-gras', gw * .12); d.text((gw - m - f.getlength(val), m * .55), val, font=f, fill=(255, 255, 255, 255))
    x0, x1, y0, y1 = m, gw - m, gh - m * .9, gh * .36
    for j in range(1, 4):
        yy = y0 - (y0 - y1) * j / 3.4; d.line([(x0, yy), (x1, yy)], fill=(255, 255, 255, 40), width=max(1, int(gw * .002)))
    n = 60
    pts = [(x0 + (x1 - x0) * j / n, y0 - (y0 - y1) * (j / n) ** 1.5 + math.sin(j / n * 13) * gh * .018 * (1 - j / n)) for j in range(int(n * g) + 1)]
    _courbe_graph(lay, d, pts, y0, couleur(e.o.get('couleur'), (52, 211, 110)), max(4, int(gw * .011)))
    im.alpha_composite(lay)
    poser(s, avec_ombre(im, max(10, W // 70), W // 90, 90), cx, cy, alpha=al, protege=True)


def anneau(taille, part, c, libelle, valeur):
    T = int(taille) * 2; im = vide(T, T); d = ImageDraw.Draw(im); ep, m = int(T * .1), int(T * .08)
    d.arc([m, m, T - m, T - m], 0, 360, fill=(255, 255, 255, 46), width=ep)
    if part > 0.002: d.arc([m, m, T - m, T - m], -90, -90 + 360 * part, fill=tuple(c) + (255,), width=ep)
    d.text((T / 2, T / 2 - T * .02), valeur, font=police('ui-gras', T * .2), fill=(255, 255, 255, 255), anchor='mm')
    d.text((T / 2, T / 2 + T * .15), libelle.upper(), font=police('mono', T * .06), fill=(255, 255, 255, 170), anchor='mm')
    return im.resize((int(taille), int(taille)), Image.LANCZOS)


def bento(s, e):
    W, H = s.W, s.H; al = borne((e.d - s.t) / 0.2) * borne(s.t / 0.12)
    if al <= 0: return
    vert = couleur(e.o.get('couleur'), (52, 211, 110)); peche = (255, 160, 122)
    q = sortie(s.t / 0.4); pw, ph = int(W * .9), int(H * .3); pcx, pcy = W / 2, H * .08 + ph / 2 + (1 - q) * H * .02
    pan = verre(s, pw, ph, W * .04, pcx, pcy, dose=0.06, sombre=0.62, flou=W / 30)
    lay = vide(pw, ph); d = ImageDraw.Draw(lay); m = pw * .05; g = douce((s.t - 0.2) / max(0.3, e.d * 0.75))
    d.text((m, m * .8), str(e.o.get('texte', 'VUES')).upper(), font=police('mono', pw * .026), fill=(255, 255, 255, 180))
    a, _, _ = nombre(e.o.get('de', '0')); b, suf, dec = nombre(e.o.get('a', e.o.get('to', '161K')))
    val = f'{a + (b - a) * g:.{dec}f}'.replace('.', ',') + suf
    f = police('ui-gras', pw * .085); d.text((pw - m - f.getlength(val), m * .45), val, font=f, fill=(255, 255, 255, 255))
    x0, x1, y0, y1 = m, pw - m, ph - m * .8, ph * .3
    for j in range(1, 4): yy = y0 - (y0 - y1) * j / 3.3; d.line([(x0, yy), (x1, yy)], fill=(255, 255, 255, 34), width=max(1, W // 1000))
    n = 80; pts = [(x0 + (x1 - x0) * j / n, y0 - (y0 - y1) * (j / n) ** 1.7 + math.sin(j / n * 17) * ph * .02 * (1 - j / n)) for j in range(int(n * g) + 1)]
    _courbe_graph(lay, d, pts, y0, vert, max(4, int(pw * .006)))
    pan.alpha_composite(lay); poser(s, pan, pcx, pcy, alpha=al * q, derriere=True)

    def tuile(i, cx, cy, tw, th, dessin):
        k = apparait(s, 0.15 + 0.12 * i, 0.4)
        if k <= 0: return
        t = verre(s, tw, th, W * .035, cx, cy, dose=0.08, sombre=0.5, flou=W / 34); dessin(t, ImageDraw.Draw(t), tw, th)
        poser(s, avec_ombre(t, max(8, W // 80), W // 120, 90), cx, cy, 0.7 + 0.3 * k, 0, al * borne(k * 2))
    dv, dl = (str(e.o.get('anneau', '29 %::part effacée')).split('::') + [''])[:2]; part = nombre(dv)[0] / 100

    def d_anneau(t, d, tw, th):
        p = sortie((s.t - .35) / .8) * part; an = anneau(tw * .86, p, peche, dl, f'{round(p * 100)} %')
        t.alpha_composite(an, (int((tw - an.width) / 2), int((th - an.height) / 2)))
    kv, kl = (str(e.o.get('kpi', '672K::vues · 7 reels')).split('::') + [''])[:2]

    def d_kpi(t, d, tw, th):
        d.text((tw * .1, th * .18), compter(kv, sortie((s.t - .45) / .8)), font=police('ui-gras', th * .36), fill=(255, 255, 255, 255))
        d.text((tw * .1, th * .7), kl.upper(), font=police('mono', th * .1), fill=(255, 255, 255, 170))
    bv, bl = (str(e.o.get('barres', '161|120|97|70|52::top reels · K vues')).split('::') + [''])[:2]; vals = [nombre(v)[0] for v in bv.split('|')]

    def d_barres(t, d, tw, th):
        d.text((tw * .1, th * .06), bl.upper(), font=police('mono', tw * .055), fill=(255, 255, 255, 170))
        lb = tw * .8 / len(vals); haut, bas = th * .2, th * .88
        for j, v in enumerate(vals):
            kk = sortie((s.t - .4 - .08 * j) / .5); hh = (bas - haut) * v / max(vals) * kk; x = tw * .1 + j * lb
            d.rounded_rectangle([x + lb * .14, bas - hh, x + lb * .86, bas], int(lb * .18), fill=(vert + (255,)) if j == 0 else (255, 255, 255, 150))
            if kk > .6: d.text((x + lb / 2, bas - hh - tw * .02), f'{v:g}', font=police('ui-gras', tw * .06), fill=(255, 255, 255, 230), anchor='md')
    tw = W * .25; esp = W * .02; ty = max(H * .5, s.vy + s.vt * 1.1)
    tuile(0, W * .15, ty + tw * .5, tw, tw, d_anneau)
    tuile(1, W * .15, ty + tw + esp + tw * .28, tw, tw * .56, d_kpi)
    tuile(2, W * .85, ty + tw * .65, tw, tw * 1.3, d_barres)


# ------------------------------------------------------------------ 43
def verre_en_place(s, x0, y0, x1, y1):
    w, h = int(x1 - x0), int(y1 - y0)
    if w < 8 or h < 8: return
    composer(s, verre(s, w, h, 72 * s.W / 2160, x0 + w / 2, y0 + h / 2, dose=0, flou=s.W / 46), x0, y0)


def carte_stat(s, cx, cy, k, prog, libelle, valeur, genre, ech=1.0):
    if k <= 0: return
    u = s.W / 2160 * ech; sc = 0.82 + 0.18 * rebond(k)
    w, h = 1760 * u * sc, 1056 * u * sc; x0, y0 = cx - w / 2, cy - h / 2 + 40 * u * (1 - k)
    verre_en_place(s, x0, y0, x0 + w, y0 + h)
    v = w / 1500; o = 20; lay = vide(w + 40, h + 40); d = ImageDraw.Draw(lay)
    fl, fg = police('ui', 44 * v), police('ui-gras', 170 * v)
    txt = compter(valeur, sortie(prog))
    ombre = vide(*lay.size); od = ImageDraw.Draw(ombre)
    for dd, c in ((od, (0, 0, 0, 150)), (d, (255, 255, 255, 235))):
        x = o + 64 * v
        for ch in libelle.upper(): dd.text((x, o + 64 * v), ch, font=fl, fill=c); x += fl.getlength(ch) + 9 * v
        dd.text((o + w - 70 * v - fg.getlength(txt), o + 40 * v), txt, font=fg, fill=c if dd is od else (255, 255, 255, 255))
    gx0, gx1, gy0, gy1 = o + 64 * v, o + w - 64 * v, o + 290 * v, o + h - 80 * v
    for j in range(3): d.line([gx0, gy0 + (gy1 - gy0) * j / 2, gx1, gy0 + (gy1 - gy0) * j / 2], fill=(255, 255, 255, 70), width=max(1, int(3 * v)))
    base = ombre.filter(ImageFilter.GaussianBlur(10 * v)); graph = vide(*lay.size); cd = ImageDraw.Draw(graph); V_ = (52, 211, 102)
    if genre == 'courbe':
        ys = [.04, .07, .10, .16, .22, .35, .52, .74, 1.0]; n = max(.02, (len(ys) - 1) * sortie(prog)); pts = []
        for i in range(int(n) + 1):
            t = min(i, n); i0 = min(int(t), len(ys) - 2); f = t - i0
            pts.append((gx0 + (gx1 - gx0) * t / (len(ys) - 1), gy1 - (gy1 - gy0) * (ys[i0] + (ys[i0 + 1] - ys[i0]) * f)))
        if len(pts) > 1:
            cd.polygon(pts + [(pts[-1][0], gy1), (pts[0][0], gy1)], fill=V_ + (70,))
            lum = vide(*lay.size); ImageDraw.Draw(lum).line(pts, fill=V_ + (255,), width=int(60 * v), joint='curve')
            graph.alpha_composite(lum.filter(ImageFilter.GaussianBlur(26 * v))); cd = ImageDraw.Draw(graph)
            cd.line(pts, fill=V_ + (255,), width=max(2, int(20 * v)), joint='curve'); ex, ey = pts[-1]
            cd.ellipse([ex - 30 * v, ey - 30 * v, ex + 30 * v, ey + 30 * v], fill=V_ + (90,)); cd.ellipse([ex - 15 * v, ey - 15 * v, ex + 15 * v, ey + 15 * v], fill=(235, 255, 240, 255))
    else:
        vals = [1.0, .71, .63, .42, .25, .2, .19]; lb = (gx1 - gx0) / len(vals)
        for i, val in enumerate(vals):
            hh = sortie(borne(prog * 1.6 - i * .1)); haut = gy1 - (gy1 - gy0) * val * hh; bx = gx0 + i * lb + lb * .16
            cd.rounded_rectangle([bx, haut, bx + lb * .68, gy1], int(18 * v), fill=V_ + (230 if i == 0 else 120,))
    base.alpha_composite(graph); base.alpha_composite(lay)
    composer(s, base, x0 - o, y0 - o)


@effet('zoom-epaule', 'La caméra plonge dans un coin, un graphique en verre apparaît près de ta tête, puis l\'autre coin avec un second graphique',
       alias=('over-the-shoulder-zoom', 'ots', 'shoulder-zoom', 'corner-zoom'))
def zoom_epaule(s, e):
    p = borne(s.t / e.d); z0 = float(e.o.get('zoom', 2.0)); gx, dx = s.vx - s.W * .17, s.vx + s.W * .19
    cles = [(0, 1.0, s.vx), (.30, 1.04, s.vx), (.46, z0, gx), (.66, z0 + .04, gx), (.76, 1.05, s.vx), (.87, z0, dx), (1.0, z0 + .04, dx)]
    z, x = 1.0, s.vx
    for (pa, za, xa), (pb, zb, xb) in zip(cles, cles[1:]):
        if pa <= p <= pb: q = douce((p - pa) / (pb - pa)); z, x = za + (zb - za) * q, xa + (xb - xa) * q; break
    zoom(s, z, x, s.vy)
    k1 = borne((p - .42) / .065) * (1 - borne((p - .66) / .055)); k2 = borne((p - .84) / .065)
    if k1 <= 0 and k2 <= 0: return
    avant = s.img.copy()
    a, b = (str(e.o.get('texte', 'Vues · ce reel|Top reels · total')).split('|') + ['', ''])[:2]
    va, vb = (str(e.o.get('a', e.o.get('to', '161K|672K'))).split('|') + ['', ''])[:2]
    carte_stat(s, s.W * .43, s.H * .255, k1, borne((p - .45) / .17), a, va, 'courbe')
    carte_stat(s, s.W * .57, s.H * .255, k2, borne((p - .86) / .14), b, vb, 'barres')
    personne_devant(s, avant)


# ------------------------------------------------------------------ 44
def bulle_message(s, y, titre, corps, a):
    u = s.W / 2160; w, h = int(1880 * u), int(330 * u)
    if a <= 0 or y + h / 2 < 0 or y - h / 2 > s.H: return
    k = 0.82 + 0.18 * rebond(a); ww, hh = int(w * k), int(h * k); xs, ys = (s.W - ww) // 2, int(y - hh / 2)
    m = int(120 * u); halo = vide(ww + 2 * m, hh + 2 * m)
    ImageDraw.Draw(halo).rounded_rectangle([m - 30 * u, m - 30 * u, m + ww + 30 * u, m + hh + 30 * u], int(100 * u), fill=(255, 250, 240, int(215 * borne(a * 2))))
    composer(s, halo.filter(ImageFilter.GaussianBlur(56 * u)), xs - m, ys - m)
    g0, h0, g1, h1 = max(0, xs), max(0, ys), min(s.W, xs + ww), min(s.H, ys + hh)
    if g1 <= g0 or h1 <= h0: return
    zone = cv2.GaussianBlur(s.img[h0:h1, g0:g1], (0, 0), 20 * u)
    yy = np.linspace(0, 1, h1 - h0, dtype=np.float32)[:, None, None]
    zone = zone * 0.22 + np.float32([252, 246, 238]) / 255 * 0.78 + (1 - yy) * 0.08
    mk = Image.new('L', (ww, hh), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, ww - 1, hh - 1], int(70 * u * k), fill=255)
    mk = np.asarray(mk, np.float32)[h0 - ys:h1 - ys, g0 - xs:g1 - xs, None] / 255 * borne(a * 2.5)
    dst = s.img[h0:h1, g0:g1]; dst[:] = dst * (1 - mk) + np.clip(zone, 0, 1) * mk
    lay = vide(ww, hh); d = ImageDraw.Draw(lay); v = k * u; al = int(255 * borne(a * 2.5))
    d.rounded_rectangle([1, 1, ww - 2, hh - 2], int(70 * v), outline=(255, 255, 255, int(170 * borne(a * 2.5))), width=max(1, int(3 * v)))
    ic = int(160 * v); dg = np.linspace(0, 1, ic, dtype=np.float32)[:, None]
    icone = np.dstack([110 - dg * 64, 232 - dg * 51, 120 - dg * 51, np.full_like(dg, 255)]).repeat(ic, 1).astype(np.uint8)
    icone = Image.fromarray(icone, 'RGBA'); im_ = Image.new('L', icone.size, 0)
    ImageDraw.Draw(im_).rounded_rectangle([0, 0, ic - 1, ic - 1], int(40 * v), fill=al); icone.putalpha(im_)
    di = ImageDraw.Draw(icone); di.ellipse([30 * v, 34 * v, 130 * v, 114 * v], fill=(255, 255, 255, al))
    di.polygon([(44 * v, 102 * v), (36 * v, 130 * v), (72 * v, 110 * v)], fill=(255, 255, 255, al))
    lay.alpha_composite(icone, (int(56 * v), int(70 * v)))
    d.text((262 * v, 76 * v), titre, font=police('ui-gras', 72 * v), fill=(28, 28, 30, al))
    d.text((262 * v, 170 * v), corps, font=police('ui', 76 * v), fill=(44, 44, 46, al))
    composer(s, lay, xs, ys)


@effet('messages', 'Des notifications de messages apparaissent une à une, en verre crème avec un halo doux',
       alias=('imessage', 'texts', 'notifications', 'sms'))
def messages(s, e):
    msgs = str(e.o.get('texte', 'comment tu as monté ça ??|attends, c\'est quelle appli|envoie-moi les effets stp|EFFETS')).split('|')
    titre = e.o.get('titre', 'Messages'); n = len(msgs); u = s.W / 2160
    pas = min(0.4, e.d * 0.75 / max(1, n)); arrivees = [0.13 + i * pas for i in range(n)]
    bas = s.H * float(e.o.get('y', 0.61)); fin = borne((e.d - s.t) / 0.2)
    for k in range(n):
        if s.t < arrivees[k]: continue
        plus_recents = sum(sortie(borne((s.t - arrivees[j]) / .17)) for j in range(k + 1, n) if s.t >= arrivees[j])
        bulle_message(s, bas - 165 * u - plus_recents * 365 * u, titre, msgs[k], borne((s.t - arrivees[k]) / .17) * fin)


# ------------------------------------------------------------------ 36
@effet('taches-claude', 'Une liste de tâches Claude sous ton menton : chaque étape tourne, puis se coche en vert',
       alias=('checklist', 'tasks', 'taches', 'checklist-claude'))
def taches_claude(s, e):
    W, H = s.W, s.H; u = W / 1080; al = borne((e.d - s.t) / 0.2)
    lignes = [x.split('::') for x in str(e.o.get('texte', 'Visage repéré::chaque image|Détourage fait::masque IA|'
                                                 'Texte placé derrière toi::profondeur|Couleurs étalonnées::chaud|Rendu en 4K::2160p')).split('|')]
    n = len(lignes); cw, rh, hh = W * .9, 104 * u, 120 * u; ch = hh + rh * n + 26 * u
    y0 = min(max(s.vy + s.vt * 1.35, H * .42), H * .93 - ch); cy = y0 + ch / 2 + (1 - sortie(s.t / .35)) * H * .12
    duree = max(0.4, e.d - 0.55); fini = [0.3 + duree * (i + 1) / n for i in range(n)]
    g = verre(s, cw, ch, 40 * u, W / 2, cy, teinte=(14, 13, 16), dose=0.78, sombre=0.55, flou=30 * u); d = ImageDraw.Draw(g)
    sx, sy = 44 * u, hh / 2
    for a in range(4):
        an = a * math.pi / 2 + math.pi / 4
        d.line([(sx, sy), (sx + 18 * u * math.cos(an), sy + 18 * u * math.sin(an))], fill=CLAUDE + (255,), width=int(7 * u))
        d.line([(sx, sy), (sx + 18 * u * math.cos(an + math.pi / 4), sy + 18 * u * math.sin(an + math.pi / 4))], fill=CLAUDE + (255,), width=int(5 * u))
    d.text((80 * u, hh / 2), e.o.get('titre', 'Claude monte ton clip'), font=police('ui-gras', 42 * u), fill=BLANC + (255,), anchor='lm')
    d.text((cw - 36 * u, hh / 2), f'{sum(s.t >= t for t in fini)} sur {n}', font=police('ui', 28 * u), fill=(170, 170, 176, 255), anchor='rm')
    d.line([(30 * u, hh), (cw - 30 * u, hh)], fill=(255, 255, 255, 30), width=max(1, int(2 * u)))
    for i, (txt, meta) in enumerate([(l + [''])[:2] for l in lignes]):
        y = hh + 13 * u + rh * i + rh / 2; x, r = 56 * u, 24 * u; depart = fini[i - 1] if i else 0.3
        if s.t >= fini[i]:
            q = rebond((s.t - fini[i]) / .25); rr = r * (.6 + .4 * q)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(52, 199, 89, 255)); coche(d, x - rr * .5, y - rr * .45, rr, ep=int(5 * u))
            ct, cm = (255, 255, 255, 255), (52, 199, 89, 255)
        elif s.t >= depart:
            a0 = (s.t * 540) % 360
            d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255, 50), width=int(5 * u))
            d.arc([x - r, y - r, x + r, y + r], a0, a0 + 100, fill=CLAUDE + (255,), width=int(5 * u)); ct, cm = (255, 255, 255, 255), (170, 170, 176, 255)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255, 60), width=int(4 * u)); ct, cm = (255, 255, 255, 110), (170, 170, 176, 90)
        d.text((x + 48 * u, y), txt, font=police('ui-gras', 40 * u), fill=ct, anchor='lm')
        d.text((cw - 36 * u, y), meta, font=police('mono', 28 * u), fill=cm, anchor='rm')
    poser(s, avec_ombre(g, 24, 12, 120), W / 2, cy, 1, 0, al * borne(s.t / .12), protege=True)


# ------------------------------------------------------------------ 40
@effet('interrupteurs', 'Une carte de réglages iPhone au-dessus de toi : les interrupteurs s\'allument un par un',
       alias=('apple-toggles', 'toggles', 'reglages'))
def interrupteurs(s, e):
    lignes = str(e.o.get('texte', 'Un seul clip|Tape /effets|Zéro logiciel de montage')).split('|')
    dessous = e.o.get('pos') in ('dessous', 'below')
    if not dessous: zoom_visage(s, 1 + (float(e.o.get('zoom', 1.12)) - 1) * sortie(s.t / 0.5), 0.56)
    W = s.W; cw, rh = int(W * .72), int(W * .125); ch = rh * len(lignes); tw, th = int(W * .135), int(W * .08); tx = cw - int(W * .05) - tw

    def fond():
        im = boite(cw, ch, int(W * .055), (255, 255, 255, 250)); d = ImageDraw.Draw(im)
        for i, l in enumerate(lignes):
            d.text((W * .05, i * rh + rh / 2), l, font=police('ui', W * .048), fill=(18, 18, 20, 255), anchor='lm')
            if i: d.line([(W * .05, i * rh), (cw, i * rh)], fill=(222, 222, 226, 255), width=max(2, W // 900))
        return avec_ombre(im, max(10, W // 60), W // 90, 110), max(10, W // 60) * 2 + W // 90
    base, m = memo(e, 'fond', fond)
    moments = [float(x) - e.debut for x in str(e.o.get('moments', e.o.get('ticks'))).split('|')] if e.o.get('moments', e.o.get('ticks')) else [0.45 + 0.34 * i for i in range(len(lignes))]
    im = base.copy(); d = ImageDraw.Draw(im)
    eteint, allume = np.float32((233, 233, 235)), np.float32(couleur(e.o.get('couleur'), (52, 199, 89)))
    for i in range(len(lignes)):
        p = sortie((s.t - moments[i]) / 0.2) if i < len(moments) else 0.0
        c = tuple(int(v) for v in eteint * (1 - p) + allume * p) + (255,)
        x0, y0 = m + tx, m + i * rh + (rh - th) / 2
        d.rounded_rectangle([x0, y0, x0 + tw, y0 + th], th // 2, fill=c)
        kr = th / 2 - W * .006; kx, ky = x0 + th / 2 + (tw - th) * p, y0 + th / 2
        d.ellipse([kx - kr, ky - kr + W * .002, kx + kr, ky + kr + W * .004], fill=(0, 0, 0, 40))
        d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill=(255, 255, 255, 255))
    q = apparait(s, 0.0, 0.38); al = borne((e.d - s.t) / 0.2) * borne(s.t / 0.1)
    if dessous:
        poser(s, im, s.W / 2, min(s.H - ch * .75, s.vy + s.vt * 2.5), .6 + .4 * q, 0, al, protege=True); return
    cy = max(s.H * .08 + ch / 2, s.vy - s.vt * .95 + s.vt * float(e.o.get('chevauche', 0.08)) - ch / 2)
    poser(s, im, s.W / 2, cy + (1 - q) * s.W * .04, .6 + .4 * q, 0, al, derriere=True)
