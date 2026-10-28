"""Les effets avec tes reels : vignettes qui s'empilent, tournent, s'éventaillent, remplissent le mur."""
import math, random
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
from . import effet
from .base import (borne, sortie, douce, rebond, couleur, liste, police, mot, lignes_ajustees, boite, avec_ombre, vignette_reel,
                   varier, np_vers_pil, composer, poser, entree_sortie, apparait, memo, vide, ENCRE, OR, BLEU, CLAUDE, CREME)
from .camera import grille
from .mots import curseur, decaler
from .verre import verre, pastille_visage, coche

BLANC = (255, 255, 255)


def reels(e, largeur):
    """Les vignettes : tes captures (option images=dossier) ou des images tirées de la vidéo, chacune avec son propre look."""
    return memo(e, ('reels', largeur), lambda: [vignette_reel(varier(im, i) if e.o.get('images') is None else im, largeur) for i, im in enumerate(e.cartes)])


def grille_vignettes(cartes, cols, rangs, cel, ecart, i0=0, look=True):
    ch = int(cel * 1.25); im = vide(cols * cel + (cols - 1) * ecart, rangs * ch + (rangs - 1) * ecart)
    for k in range(cols * rangs):
        src = cartes[(i0 + k) % len(cartes)]; src = varier(src, i0 + k) if look else src.convert('RGB')
        r = max(cel / src.width, ch / src.height); t = src.resize((max(cel, int(src.width * r)), max(ch, int(src.height * r))), Image.LANCZOS)
        g, h = (t.width - cel) // 2, int((t.height - ch) * .3); t = t.crop((g, h, g + cel, h + ch)).convert('RGBA')
        m = Image.new('L', t.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, cel - 1, ch - 1], max(4, cel // 12), fill=255); t.putalpha(m)
        im.alpha_composite(t, ((k % cols) * (cel + ecart), (k // cols) * (ch + ecart)))
    return im


# ------------------------------------------------------------------ 1
@effet('avalanche', 'Tes reels s\'empilent derrière ta tête, un tous les quarts de seconde', alias=('noise', 'the-noise', 'pile'), cartes=True)
def avalanche(s, e):
    cartes = reels(e, int(s.W * float(e.o.get('taille', e.o.get('size', .34)))))
    pos = memo(e, 'pos', lambda: [(r.uniform(.14, .86), r.uniform(.12, .52), r.uniform(-7, 7)) for r in [random.Random(7)] for _ in range(min(16, max(4, int(e.d / .22))))])
    fin = borne((e.d - s.t) / .2)
    for i, (x, y, r) in enumerate(pos):
        t0 = i * .22
        if s.t < t0: break
        poser(s, cartes[i % len(cartes)], x * s.W, y * s.H, .6 + .4 * rebond((s.t - t0) / .25), r, borne((s.t - t0) / .08) * fin, derriere=True)


# ------------------------------------------------------------------ 4
@effet('orbite', 'Tes reels tournent autour de ta tête : devant en bas, derrière en haut', alias=('orbit',), cartes=True)
def orbite(s, e):
    K = int(e.o.get('nombre', e.o.get('count', 6))); cartes = reels(e, int(s.W * float(e.o.get('taille', e.o.get('size', .2)))))
    intro, fin = sortie(s.t / .4), borne((e.d - s.t) / .25)
    rx, ry, oy = s.W * .38 * intro, max(s.vt * 1.5, s.H * .1), s.vy + s.vt * .9
    items = sorted((math.sin(i * 2 * math.pi / K + s.t * float(e.o.get('vitesse', e.o.get('speed', 1.9)))), i * 2 * math.pi / K + s.t * float(e.o.get('vitesse', e.o.get('speed', 1.9))), i) for i in range(K))
    for prof, th, i in items:
        poser(s, cartes[i % len(cartes)], s.vx + rx * math.cos(th), oy + ry * math.sin(th), (.78 + .24 * (prof + 1) / 2) * (.5 + .5 * intro),
              -6 * math.cos(th), fin * borne(s.t / .15), derriere=prof < 0, protege=prof >= 0)


# ------------------------------------------------------------------ 38
@effet('carrousel', 'Tes reels tournent autour de toi en carrousel 3D, puis ralentissent', alias=('carousel-spin', 'carousel'), cartes=True)
def carrousel(s, e):
    K = int(e.o.get('nombre', e.o.get('count', max(6, min(12, len(e.cartes)))))); cw = int(s.W * float(e.o.get('taille', e.o.get('size', .3))))

    def fabrique():
        out = []
        for f in reels(e, cw):
            a = np.asarray(f).copy(); a[..., :3] = (a[..., :3] * .55).astype(np.uint8); out.append((f, Image.fromarray(a, 'RGBA')))
        return out
    cartes = memo(e, 'cartes3d', fabrique)
    k = entree_sortie(s, e, .3, .25); xx, yy = grille(s)
    d = ((xx - s.vx) / (s.W * .55)) ** 2 + ((yy - (s.vy + s.H * .15)) / (s.H * .5)) ** 2
    s.img *= ((1 - k * .5 * np.clip(d, 0, 1) - k * .12) * (1 - s.masque) + s.masque)[..., None]
    p = borne(s.t / e.d); tour = float(e.o.get('tours', e.o.get('turns', 1.1))) * 2 * math.pi * (1 - (1 - p) ** 2.4)
    intro, fin = sortie(s.t / .45), borne((e.d - s.t) / .25); R, ry, cy = s.W * .56 * intro, s.H * .07, s.vy + s.vt * 1.8
    n = len(cartes)
    for prof, th, i in sorted((math.cos(i * 2 * math.pi / K + tour), i * 2 * math.pi / K + tour, i) for i in range(K)):
        f, sombre = cartes[(i * (3 if n % 3 else 2)) % n]; src = f if prof >= 0 else sombre
        sx = max(.06, abs(math.cos(th)) ** .6); ech = (.72 + .34 * (prof + 1) / 2) * (.5 + .5 * intro)
        poser(s, src.resize((max(2, int(src.width * ech * sx)), max(2, int(src.height * ech))), Image.BILINEAR), s.vx + R * math.sin(th), cy + ry * prof,
              1, 0, fin * borne(s.t / .12) * (.85 + .15 * prof), derriere=prof < 0, protege=prof >= 0)


# ------------------------------------------------------------------ 33
@effet('eventail-telephones', 'Tes reels s\'ouvrent comme un jeu de cartes de téléphones, sous un titre', alias=('phone-fan', 'fan', 'telephones'), cartes=True)
def eventail_telephones(s, e):
    W, H = s.W, s.H; al = borne((e.d - s.t) / .2); lignes = liste(e.o.get('texte'), '45 effets.|zéro logiciel de montage.')
    T = memo(e, 'taille', lambda: lignes_ajustees(lignes, W * .84, 'ui-gras', int(W * .08)))
    y = max(H * .06, s.vy - s.vt * 1.3 - T * 1.3 * len(lignes))
    for j, l in enumerate(lignes):
        kj = borne((s.t - .05 - .1 * j) / .18); der = j == len(lignes) - 1
        t = memo(e, ('t', j), lambda: mot(l, T, 'ui-gras', (16, 16, 18) if der else BLANC, ombre=0 if der else 9))
        if der: composer(s, boite(t.width - T * .15, T * 1.22, T * .08, (255, 255, 255, 255)), W / 2 - (t.width - T * .15) / 2, y, al * kj, protege=True)
        poser(s, t, W / 2, y + T * .6, 1, 0, al * kj, protege=True); y += T * 1.3
    pw = int(W * .23); ph = int(pw * 2.0)

    def tel(i):
        im = boite(pw, ph, pw * .16, (14, 14, 16, 255))
        ecran = vignette_reel(varier(e.cartes[i % len(e.cartes)], i) if e.o.get('images') is None else e.cartes[i % len(e.cartes)], pw - 10, ombre=False)
        ecran = ecran.resize((pw - 10, ph - 10)); im.alpha_composite(ecran, (5, 5))
        ImageDraw.Draw(im).rounded_rectangle([pw * .36, ph * .025, pw * .64, ph * .045], pw * .03, fill=(0, 0, 0, 255))
        return avec_ombre(im, 14, 8, 120)
    tels = memo(e, 'tels', lambda: [tel(i) for i in range(4)])
    cx = W / 2 * .5 + s.vx * .5; cy = min(max(s.vy + s.vt * 1.1 + ph / 2, H * .62), H - ph * .42)
    for i, o in enumerate((-1.5, -.5, .5, 1.5)):
        q = rebond((s.t - .2 - .06 * i) / .4)
        poser(s, tels[i], cx + o * W * .19 * q, cy + o * o * W * .025 * q, .9, -o * 11 * q, al * borne((s.t - .2) / .1), protege=True)


# ------------------------------------------------------------------ 32
@effet('broll-partage', 'Écran partagé : un B-roll en haut avec une étiquette, toi en bas', alias=('broll-split', 'broll', 'b-roll'), cartes=True)
def broll_partage(s, e):
    W, H = s.W, s.H; k = sortie(s.t / .3) * borne((e.d - s.t) / .2); al = borne((e.d - s.t) / .2)
    decaler(s, (H * .72 - s.vy) * k); hh = int(H * .5 * k)
    if hh > 2:
        src = e.cartes[int(e.o.get('choix', e.o.get('pick', 0))) % len(e.cartes)].convert('RGB')
        z = 1 + .06 * borne(s.t / e.d); tw, th = int(W * z), int(H * .5 * z); r = max(tw / src.width, th / src.height)
        im = src.resize((int(src.width * r) + 1, int(src.height * r) + 1), Image.BILINEAR)
        g, h = (im.width - W) // 2, int((im.height - H * .5) * .35); haut = np.asarray(im.crop((g, h, g + W, h + int(H * .5))), np.float32) / 255
        s.img[:hh] = haut[int(H * .5) - hh:]; s.masque[:hh] = 0; s.img[max(0, hh - 3):hh + 3] = np.float32(OR) / 255
    tag = memo(e, 'tag', lambda: mot(str(e.o.get('texte', '4 h  →  4 min')), W * .06, 'ui-gras', (16, 16, 18)))
    tw, th = int(tag.width + W * .11), int(tag.height * 1.25); et = vide(tw, th); d = ImageDraw.Draw(et); n = th * .5
    d.polygon([(0, th / 2), (n, 0), (tw, 0), (tw, th), (n, th)], fill=(255, 255, 255, 255))
    d.ellipse([n * .55, th / 2 - n * .16, n * .87, th / 2 + n * .16], fill=(200, 200, 205, 255)); et.alpha_composite(tag, (int(n * 1.05), (th - tag.height) // 2))
    poser(s, avec_ombre(et, 12, 6, 110), W * .66, H * .39 * k, .5 + .5 * apparait(s, .3), 8, al * borne((s.t - .3) / .08))


# ------------------------------------------------------------------ 27
_papier = {}


@effet('pastilles', 'Pièce en papier quadrillé, tes reels épinglés derrière toi, un curseur clique des pastilles bleues', alias=('check-pills', 'pills'), cartes=True)
def pastilles(s, e):
    W, H = s.W, s.H; k = entree_sortie(s, e, .15, 0); m = s.masque[..., None]; al = borne((e.d - s.t) / .2)
    if (W, H) not in _papier:
        g = np.ones((H, W, 3), np.float32) * np.float32([.935, .945, .96]); pas, ep = max(20, W // 20), max(1, W // 700)
        for x in range(0, W, pas): g[:, x:x + ep] = np.float32([.86, .875, .9])
        for y in range(0, H, pas): g[y:y + ep] = np.float32([.86, .875, .9])
        _papier[(W, H)] = g
    s.img = s.img * (1 - k) + (s.img * m + _papier[(W, H)] * (1 - m)) * k

    def tableau(i, titre):
        bw = int(W * .44); im = boite(bw, bw * 1.12, bw * .07, (255, 255, 255, 255)); d = ImageDraw.Draw(im)
        d.ellipse([bw * .06, bw * .055, bw * .15, bw * .145], fill=OR + (255,))
        d.text((bw * .19, bw * .1), titre, font=police('ui-gras', bw * .06), fill=(20, 20, 22, 255), anchor='lm')
        gr = grille_vignettes(e.cartes, 3, 3, int(bw * .28), int(bw * .025), i0=i * 3); im.alpha_composite(gr, ((bw - gr.width) // 2, int(bw * .2)))
        return avec_ombre(im, 16, 8, 70)
    t1 = memo(e, 't1', lambda: tableau(0, e.o.get('compte', '@idrisstechinsider'))); t2 = memo(e, 't2', lambda: tableau(1, e.o.get('tableau', 'Reels  ·  45 effets')))
    by = max(H * .17, s.vy - s.vt * .9)
    poser(s, t1, W * .25, by, .6 + .4 * apparait(s, 0), 8, al * borne(s.t / .1), derriere=True)
    poser(s, t2, W * .76, by - W * .02, .6 + .4 * apparait(s, .1), -8, al * borne((s.t - .1) / .1), derriere=True)
    noms = liste(e.o.get('texte'), 'Accroche|Sous-titres|Coupes|B-roll')
    places = [(-.95, 2.35), (.55, 2.0), (-.35, 2.95), (.95, 2.75), (.1, 3.45), (-1.1, 3.3)]
    ph = W * .078; cu = memo(e, 'curseur', lambda: curseur(W * .055)); pos = []
    for i, n in enumerate(noms):
        sx, sy = places[i % len(places)]; x = borne(s.vx + sx * s.vt * 1.6, W * .16, W * .84); y = borne(s.vy + sy * s.vt, H * .3, H * .9)
        t0 = .22 + .2 * i; pos.append((x, y, t0))
        if s.t < t0: continue
        clique = s.t >= t0 + .12
        t = mot(n, ph * .42, 'ui-gras', BLANC); pw = int(t.width + ph * (.75 if clique else .35))
        pi = boite(pw, ph, ph / 2, BLEU + (255,)); pi.alpha_composite(t, (int(ph * .18), int((ph - t.height) / 2)))
        if clique: coche(ImageDraw.Draw(pi), pw - ph * .55, ph * .33, ph * .33)
        poser(s, avec_ombre(pi, 10, 5, 90), x, y, (.5 + .5 * apparait(s, t0, .25)) * (1 - .1 * math.sin(math.pi * borne((s.t - t0 - .12) / .2))), 0, al, protege=True)
    if pos and s.t > pos[0][2] - .1:
        fait = [p for p in pos if p[2] <= s.t + .1]; tx, ty, t0 = fait[-1]
        px, py = (pos[len(fait) - 2][0], pos[len(fait) - 2][1]) if len(fait) > 1 else (W * .9, H * .95); q = douce((s.t - (t0 - .12)) / .2)
        poser(s, cu, px + (tx - px) * q + ph * .3 + cu.width / 2, py + (ty - py) * q + ph * .1 + cu.height / 2, 1, 0, al)


# ------------------------------------------------------------------ 17
@effet('pluie-touches', 'Des touches de clavier tombent en pluie derrière toi', alias=('shortcut-rain', 'rain', 'pluie'))
def pluie_touches(s, e):
    touches = liste(e.o.get('texte'), 'cmd|/|C|V|Z|échap|tab|maj|entrée|opt'); ks = int(s.W * .1)

    def touche(t):
        f = police('mono', ks * .36); w = max(ks, int(f.getlength(t) + ks * .5))
        im = boite(w, ks, ks * .18, (190, 190, 198, 255)); im.alpha_composite(boite(w - 8, ks - 14, ks * .16, (246, 246, 248, 255)), (4, 3))
        ImageDraw.Draw(im).text((w / 2, ks * .44), t, font=f, fill=ENCRE + (255,), anchor='mm'); return avec_ombre(im, 8, 6, 100)
    tt = memo(e, 'touches', lambda: [touche(t) for t in touches])
    parts = memo(e, 'parts', lambda: [(random.Random(i).random(), random.Random(i + 99).random() * max(.1, e.d - .8), .45 + .4 * random.Random(i + 7).random(),
                                       random.Random(i + 3).uniform(-25, 25), random.Random(i + 5).uniform(-60, 60)) for i in range(int(e.o.get('nombre', e.o.get('count', 26))))])
    for i, (x, t0, v, r0, w) in enumerate(parts):
        if s.t >= t0:
            poser(s, tt[i % len(tt)], s.W * (.04 + .92 * x), -ks + (s.t - t0) * v * s.H, .75 + .35 * v, r0 + w * (s.t - t0), borne((e.d - s.t) / .2), derriere=True)


# ------------------------------------------------------------------ 30
@effet('mur-profil', 'Ta grille de profil remplit le mur derrière toi pendant qu\'un compteur défile', alias=('profile-wall', 'wall'), cartes=True)
def mur_profil(s, e):
    W, H = s.W, s.H; al = borne((e.d - s.t) / .2)

    def mur():
        pw, ph = int(W * .92), int(H * .36); im = boite(pw, ph, W * .035, (16, 16, 18, 240)); d = ImageDraw.Draw(im)
        for j, o in enumerate(('Publications', 'Reels', 'Identifié')):
            x = pw * (.2 + .3 * j); d.text((x, ph * .06), o, font=police('ui', W * .03), fill=(255, 255, 255, 255) if j == 1 else (130, 130, 136, 255), anchor='mm')
            if j == 1: d.rectangle([x - pw * .08, ph * .1, x + pw * .08, ph * .1 + 4], fill=(255, 255, 255, 255))
        gr = grille_vignettes(e.cartes, 4, 2, int(pw * .225), int(pw * .012), look=False); im.alpha_composite(gr, ((pw - gr.width) // 2, int(ph * .14)))
        return avec_ombre(im, 20, 10, 110)
    mr = memo(e, 'mur', mur)
    poser(s, mr, W / 2, H * .04 + mr.height / 2, .94 + .06 * sortie(s.t / .35), 0, al * borne(s.t / .15), derriere=True)
    cw, chh = W * .76, W * .25; cy = min(H * .86, s.vy + s.vt * 2.6)
    g = verre(s, cw, chh, chh * .18, W / 2, cy, teinte=(12, 12, 14), dose=.5, sombre=.45); d = ImageDraw.Draw(g)
    cible = int(e.o.get('nombre', e.o.get('count', 161000))); n = int(cible * sortie((s.t - .2) / .8)); bascule = borne((s.t - 1.15) / .2)
    if bascule < 1: d.text((cw / 2, chh * .33), f'{n:,}'.replace(',', ' '), font=police('ui-gras', chh * .3), fill=(255, 255, 255, int(255 * (1 - bascule))), anchor='mm')
    if bascule > 0: d.text((cw / 2, chh * .33), str(e.o.get('libelle', 'vues')), font=police('ui-gras', chh * .3), fill=(255, 255, 255, int(255 * bascule)), anchor='mm')
    av = pastille_visage(s, e, chh * .3); g.alpha_composite(av, (int(chh * .14), int(chh * .58)))
    d.text((chh * .52, chh * .68), e.o.get('nom', 'idrisstechinsider'), font=police('ui-gras', chh * .09), fill=(255, 255, 255, 255), anchor='lm')
    d.text((chh * .52, chh * .8), e.o.get('sous', 'meilleur reel'), font=police('ui', chh * .075), fill=(170, 170, 176, 255), anchor='lm')
    suivi = s.t >= e.d * .7
    d.rounded_rectangle([cw - chh * .95, chh * .62, cw - chh * .14, chh * .86], chh * .12, fill=(60, 60, 66, 255) if suivi else (255, 255, 255, 255))
    d.text((cw - chh * .545, chh * .74), 'Abonné' if suivi else 'Suivre', font=police('ui-gras', chh * .08), fill=(255, 255, 255, 255) if suivi else (16, 16, 18, 255), anchor='mm')
    poser(s, g, W / 2, cy + (1 - sortie((s.t - .05) / .3)) * H * .1, 1, 0, al * borne((s.t - .05) / .12), protege=True)


# ------------------------------------------------------------------ 45
def icone_vues(px):
    k = px / 24; im = vide(34 * k, 24 * k); d = ImageDraw.Draw(im)
    d.arc([2 * k, 2 * k, 32 * k, 26 * k], 200, 340, fill=(255, 255, 255, 255), width=max(2, int(3 * k)))
    d.polygon([(17 * k, 8 * k), (24 * k, 17 * k), (17 * k, 23 * k), (10 * k, 17 * k)], fill=(255, 255, 255, 255))
    return im


def tuile_grille(im, w, h, vues, r):
    t = im.convert('RGB'); k = max(w / t.width, h / t.height); t = t.resize((int(t.width * k) + 1, int(t.height * k) + 1), Image.LANCZOS)
    t = t.crop(((t.width - w) // 2, (t.height - h) // 2, (t.width - w) // 2 + w, (t.height - h) // 2 + h)).convert('RGBA')
    mk = Image.new('L', (w, h), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
    if vues:
        u = w / 660; fd = Image.linear_gradient('L').resize((w, int(h * .28))).point(lambda v: int(v * .75))
        om = vide(*fd.size); om.putalpha(fd); t.alpha_composite(om, (0, h - fd.height))
        ic = icone_vues(int(56 * u)); x, y = int(34 * u), int(h - 92 * u); t.alpha_composite(ic, (x, y + int(2 * u)))
        ImageDraw.Draw(t).text((x + ic.width + 14 * u, y - 6 * u), vues, font=police('ui-gras', 58 * u), fill=(255, 255, 255, 255))
    t.putalpha(mk); ImageDraw.Draw(t).rounded_rectangle([1, 1, w - 2, h - 2], r, outline=(255, 255, 255, 150), width=max(1, int(4 * w / 660)))
    return t


@effet('grille-profil', 'Tu rétrécis au centre de ta grille 3x3, tes reels apparaissent autour avec leurs vues', alias=('place-in-grid', 'grid', 'profile-grid'), cartes=True)
def grille_profil(s, e):
    W, H = s.W, s.H; g, mg = int(33 * W / 2160), int(68 * W / 2160)
    tw = (W - 2 * mg - 2 * g) // 3; th = int(tw * 16 / 9); haut = (H - (3 * th + 2 * g)) // 2; r = int(28 * W / 2160)
    rect = lambda i: (mg + (i % 3) * (tw + g), haut + (i // 3) * (th + g))
    vues = liste(e.o.get('vues'), '161K|58K|44K|39K|31K|27K|22K|18K|12K')
    tuiles = memo(e, 'tuiles', lambda: [tuile_grille(varier(im, i) if e.o.get('images') is None else im, tw, th, vues[i % len(vues)], r) for i, im in enumerate((e.cartes * 8)[:8])])
    moi = s.img.copy(); p = douce(borne(s.t / .45))
    flou = cv2.resize(cv2.GaussianBlur(cv2.resize(moi, (W // 8, H // 8)), (0, 0), 14), (W, H), interpolation=cv2.INTER_CUBIC)
    lum = (flou @ np.float32([.299, .587, .114]))[..., None]; flou = np.clip(lum + (flou - lum) * 1.25, 0, 1)
    s.img = flou * .63 + np.float32([255, 248, 238]) / 255 * .37
    for j, place in enumerate((1, 5, 7, 3, 2, 8, 6, 0)):
        a = borne((s.t - .47 - j / 30) / .1)
        if a > 0: x, y = rect(place); poser(s, tuiles[j], x + tw / 2, y + th / 2, .82 + .18 * rebond(a), 0, borne(a * 2))
    cx, cy = rect(4); w2, h2 = int(W + (tw - W) * p), int(H + (th - H) * p)
    composer(s, tuile_grille(np_vers_pil(moi), w2, h2, vues[8 % len(vues)] if p > .9 else None, int(r * p)), cx * p, cy * p)
    if p > .95:
        c = vide(tw + 8, th + 8); ImageDraw.Draw(c).rounded_rectangle([2, 2, tw + 5, th + 5], r + 2, outline=OR + (255,), width=8); composer(s, c, cx - 4, cy - 4)
