"""Les effets de texte : mots géants, titres, couvertures, tampons, enseignes, listes."""
import math, random
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
from . import effet
from .base import (borne, sortie, douce, rebond, couleur, liste, police, mot, mot_ajuste, lignes_ajustees, boite, avec_ombre,
                   pil_vers_np, etalonner, composer, poser, zoom_visage, assombrir_bords, entree_sortie, apparait, memo, vide,
                   CREME, ENCRE, OR, BLEU, ROUGE, VERT, CLAUDE, NUIT)
from .camera import grille, trace, courbe, pointe
from .verre import pastille_visage, coche

BLANC = (255, 255, 255)


def curseur(t):
    t = float(t); im = vide(t * .95, t * 1.45); d = ImageDraw.Draw(im)
    pts = [(3, 3), (3, t * 1.12), (t * .3, t * .87), (t * .5, t * 1.33), (t * .66, t * 1.26), (t * .46, t * .8), (t * .82, t * .8)]
    d.polygon(pts, fill=(255, 255, 255, 255)); d.line(pts + [pts[0]], fill=(0, 0, 0, 255), width=max(2, int(t / 14)), joint='curve')
    return avec_ombre(im, 6, 3, 110)


def decaler(s, dy):
    """Fait glisser toute l'image (et toi) vers le bas de dy pixels."""
    if abs(dy) < 0.5: return
    M = np.float32([[1, 0, 0], [0, 1, dy]])
    s.img = cv2.warpAffine(s.img, M, (s.W, s.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    s.masque = cv2.warpAffine(s.masque, M, (s.W, s.H)); s.vy += dy


def espace(txt, taille, style, c, ecart):
    f = police(style, taille); w = sum(f.getlength(ch) for ch in txt) + ecart * max(0, len(txt) - 1)
    bb = f.getbbox('Ag'); im = vide(w + 8, bb[3] - bb[1] + taille * .4); d = ImageDraw.Draw(im); x = 4
    for ch in txt: d.text((x, -bb[1] + taille * .2), ch, font=f, fill=tuple(c) + (255,)); x += f.getlength(ch) + ecart
    return im


# ------------------------------------------------------------------ 6
@effet('mot-geant', 'Un mot géant tombe derrière toi', alias=('backdrop-word', 'backdrop', 'mot-fond'))
def mot_geant(s, e):
    im = memo(e, 'mot', lambda: mot_ajuste(str(e.o.get('texte', 'KARATOU')), s.W * .94, e.o.get('police', 'impact'),
                                            fill=couleur(e.o.get('couleur', e.o.get('color')), CREME), ombre=10))
    k = rebond(s.t / 0.42); y_fin = s.vy - s.vt * 1.05
    poser(s, im, s.W / 2 * .6 + s.vx * .4, -im.height + (y_fin + im.height) * k, alpha=borne((e.d - s.t) / .2), derriere=True)


# ------------------------------------------------------------------ 8
@effet('ticket', 'Tes consignes s\'impriment comme un ticket de caisse, dans le mur au-dessus de ta tête', alias=('the-bill', 'bill', 'recu'))
def ticket(s, e):
    lignes = str(e.o.get('texte', 'COMMANDE N°1021|1x orbite|1x projecteur|1x plongée|coupe les blancs|TOTAL : 1 prompt')).split('|')

    def fabrique():
        pw = int(s.W * .5); lh = int(pw * .085); m = int(pw * .08)
        im = Image.new('RGBA', (pw, m * 2 + lh * (len(lignes) + 1)), CREME + (255,)); d = ImageDraw.Draw(im); f = police('mono', lh * .62)
        for i, l in enumerate(lignes):
            der = i == len(lignes) - 1; y = m + lh * i + (lh if der else 0)
            if der:
                for x in range(m, pw - m, 14): d.line([(x, y - lh * .45), (x + 7, y - lh * .45)], fill=ENCRE + (140,), width=2)
            d.text((m, y), l, font=f, fill=ENCRE + (255,))
        return im
    rec = memo(e, 'rec', fabrique)
    fente_y = s.H * .075; ech = min(1.0, max(80, s.vy - s.vt * 1.3 - fente_y) / rec.height)
    L = int(rec.height * douce(s.t / (e.d * .75))); al = borne((e.d - s.t) / .25)
    if L > 2:
        z = 14; papier = vide(rec.width, L + z); papier.paste(rec.crop((0, 0, rec.width, L)), (0, 0))
        ImageDraw.Draw(papier).polygon([(x, L) for x in range(0, rec.width + 1, 2 * z)] + [(rec.width, L)] +
                                       [(x + z, L + z) for x in range(rec.width - 2 * z, -1, -2 * z)], fill=CREME + (255,))
        papier = avec_ombre(papier, 10, 6, 90)
        if ech < 1: papier = papier.resize((int(papier.width * ech), int(papier.height * ech)), Image.BILINEAR)
        composer(s, papier, s.W / 2 - papier.width / 2, fente_y - 10 * ech, al, derriere=True)
    fente = boite(s.W * .62, s.H * .03, s.H * .015, (30, 30, 34, 255), (90, 90, 96, 255), 3)
    poser(s, avec_ombre(fente, 10, 6, 140), s.W / 2, fente_y, alpha=al * borne(s.t / .15), derriere=True)


# ------------------------------------------------------------------ 18
@effet('tampon', 'Un gros tampon rouge s\'écrase sur l\'image', alias=('reject-stamp', 'stamp', 'refuse'))
def tampon(s, e):
    txt = str(e.o.get('texte', 'REFUSÉ')).upper(); c = couleur(e.o.get('couleur', e.o.get('color')), (214, 40, 40))

    def fabrique():
        t = mot_ajuste(txt, s.W * .62, 'impact', 200, fill=c); m = int(t.height * .12)
        im = vide(t.width + 4 * m, t.height + 2 * m)
        ImageDraw.Draw(im).rounded_rectangle([3, 3, im.width - 4, im.height - 4], 18, outline=c + (255,), width=max(6, m // 2))
        im.alpha_composite(t, (2 * m, m))
        a = np.asarray(im.split()[3], np.float32) * np.clip(np.random.default_rng(3).uniform(.55, 1.6, (im.height, im.width)), 0, 1)
        im.putalpha(Image.fromarray(a.astype(np.uint8))); return im
    st = memo(e, 'st', fabrique); k = borne(s.t / .16)
    if .16 < s.t < .45:   # la secousse de l'impact
        a = (.45 - s.t) / .29 * s.W * .012; r = np.random.default_rng(int(s.temps * 30))
        s.img = cv2.warpAffine(s.img, np.float32([[1, 0, r.uniform(-a, a)], [0, 1, r.uniform(-a, a)]]), (s.W, s.H), borderMode=cv2.BORDER_REFLECT)
    y = borne(float(e.o['y']) * s.H if 'y' in e.o else s.vy + s.vt * 2.7, 0, s.H * .85)
    poser(s, st, s.W / 2, y, 2.3 - 1.3 * k * k, float(e.o.get('angle', 12)), k * borne((e.d - s.t) / .2), protege=True)


# ------------------------------------------------------------------ 19
@effet('compte-a-rebours', 'Une horloge à volets 3, 2, 1 au-dessus de ta tête', alias=('countdown-flip', 'countdown', 'rebours'))
def compte_a_rebours(s, e):
    n0 = int(e.o.get('depuis', e.o.get('from', 3))); seg = e.d / n0
    i = min(n0 - 1, int(s.t / seg)); act, prec = n0 - i, n0 - i + 1
    f = borne((s.t - i * seg) / .3) if i > 0 else 1.0
    tw, th = int(s.W * .3), int(s.W * .38)

    def moitie(n, haut):
        im = boite(tw, th, tw * .1, (30, 30, 34, 255))
        ImageDraw.Draw(im).text((tw / 2, th / 2), str(n), font=police('impact', th * .62), fill=CREME + (255,), anchor='mm')
        return im.crop((0, 0, tw, th // 2)) if haut else im.crop((0, th // 2, tw, th))
    m = memo(e, 'moities', lambda: {(n, h): moitie(n, h) for n in range(0, n0 + 2) for h in (True, False)})
    im = vide(tw, th); im.paste(m[(act, True)], (0, 0)); im.paste(m[(prec if f < 1 else act, False)], (0, th // 2))
    if f < .5:
        h = max(1, int(th / 2 * (1 - 2 * f))); im.paste(m[(prec, True)].resize((tw, h)), (0, th // 2 - h))
    elif f < 1:
        h = max(1, int(th / 2 * (2 * f - 1))); im.paste(m[(act, False)].resize((tw, h)), (0, th // 2))
    ImageDraw.Draw(im).line([(0, th // 2), (tw, th // 2)], fill=(0, 0, 0, 255), width=4)
    poser(s, avec_ombre(im, 16, 10, 120), s.W / 2 * .6 + s.vx * .4, max(th / 2 + s.H * .05, s.vy - s.vt * 2.3),
          .7 + .3 * rebond(s.t / .3), 0, borne((e.d - s.t) / .2), derriere=True)


# ------------------------------------------------------------------ 21 (+ look=editorial)
@effet('couverture', 'Tu deviens la couverture d\'un magazine, le titre derrière ta tête (look=editorial pour la version classique)',
       alias=('cover-star', 'cover', 'magazine'))
def couverture(s, e):
    if e.o.get('look') in ('editorial', 'éditorial'): return couverture_editoriale(s, e)
    k = sortie(s.t / .35); al = borne((e.d - s.t) / .2)
    s.img = s.img * (1 - .6 * k) + etalonner(s.img, 'vif') * .6 * k
    c = couleur(e.o.get('couleur', e.o.get('color')), ROUGE)
    titre = memo(e, 'titre', lambda: mot_ajuste(str(e.o.get('texte', 'IDRISS')).upper(), s.W * .92, 'impact', 600, fill=c))
    th = min(titre.height, s.H * .24)
    poser(s, titre, s.W / 2, s.H * .035 + th / 2 - (1 - k) * th, th / titre.height, 0, al * k, derriere=True)
    num = memo(e, 'num', lambda: mot(str(e.o.get('numero', 'LE NUMÉRO IA  ·  2026')), s.W * .025, 'mono', BLANC, ombre=3))
    poser(s, num, s.W / 2, s.H * .03, alpha=al * k, derriere=True)
    y = s.H * .5
    for j, l in enumerate(liste(e.o.get('lignes'), '45 effets|à copier|sans logiciel|de montage')):
        gros = j == 0
        im = memo(e, ('l', j), lambda: mot(l, s.W * (.085 if gros else .045), 'italique' if gros else 'impact', OR if gros else BLANC, ombre=5))
        kj = sortie((s.t - .15 - .08 * j) / .3)
        composer(s, im, s.W * .05 - (1 - kj) * 60, y, al * kj, protege=True); y += im.height * .86

    def code_barres():
        r = random.Random(1); bw, bh = int(s.W * .16), int(s.W * .09)
        im = Image.new('RGBA', (bw, bh), (255, 255, 255, 255)); d = ImageDraw.Draw(im); x = 8
        while x < bw - 8:
            w = r.choice((2, 2, 3, 5)); d.rectangle([x, 6, x + w - 1, bh - 18], fill=(0, 0, 0, 255)); x += w + r.choice((2, 3, 4))
        return im
    cb = memo(e, 'cb', code_barres)
    composer(s, cb, s.W * .95 - cb.width, s.H * .93 - cb.height, al * k, protege=True)


def couverture_editoriale(s, e):
    k = sortie(s.t / .35); al = borne((e.d - s.t) / .2); W, H = s.W, s.H
    lum = (s.img @ np.float32([.299, .587, .114]))[..., None]
    doux = (s.img * .82 + lum * .18) * .9 + np.float32((252, 238, 228)) / 255 * .1
    eclat = cv2.GaussianBlur(cv2.resize(np.clip(s.img[::4, ::4] - .62, 0, 1), (W, H)), (0, 0), W * .012)
    s.img = s.img * (1 - k) + np.clip(doux + eclat * .55, 0, 1) * k
    encre, rose, creme = couleur(e.o.get('couleur'), (26, 20, 22)), couleur(e.o.get('accent'), (168, 70, 94)), (252, 244, 236)
    titre = str(e.o.get('texte', 'EFFETS')).upper()

    def tete():
        t = int(H * .16)
        while t > 20 and police('serif', t).getlength(titre) + t * .04 * len(titre) > W * .92: t = int(t * .95)
        return espace(titre, t, 'serif', encre, t * .04)
    m = memo(e, 'tete', tete)
    poser(s, m, W / 2, H * .085 + m.height / 2, 1.05 - .05 * sortie(s.t / .5), 0, al * k, derriere=True)
    num = memo(e, 'num', lambda: espace(str(e.o.get('numero', 'LE NUMÉRO UN SEUL CLIP  ·  N°45  ·  OCTOBRE 2026')), int(W * .022), 'ui', encre, W * .006))
    poser(s, num, W / 2, H * .075, alpha=al * k, derriere=True)
    poser(s, memo(e, 'trait', lambda: boite(W * .86, max(3, W // 600), 1, encre + (255,))), W / 2, H * .087 + m.height, alpha=al * k * .8, derriere=True)
    styles = [('italique', .085, encre), ('serif', .105, rose), ('ui', .03, encre)]
    y = H * float(e.o.get('lignes_y', 0.575))
    for j, l in enumerate(liste(e.o.get('lignes'), 'Un clip,|45 looks.|SANS MONTEUR  ·  SANS APPLI')):
        st, tl, c = styles[min(j, 2)]
        im = memo(e, ('l', j), lambda: espace(l, int(W * tl), st, c, W * .006) if st == 'ui' else mot(l, W * tl, st, c, halo=(creme, W * .012)))
        kj = sortie((s.t - .2 - .1 * j) / .35)
        composer(s, im, W * .05 - (1 - kj) * W * .03, y, al * kj); y += im.height * (.82 if st != 'ui' else 1.6)
    y = H * float(e.o.get('droite_y', 0.715))
    for j, l in enumerate(liste(e.o.get('droite'), 'l\'art du|montage sans effort')):
        im = memo(e, ('d', j), lambda: mot(l, W * .058, 'italique', encre, halo=(creme, W * .01)))
        kj = sortie((s.t - .45 - .1 * j) / .35)
        composer(s, im, W * .95 - im.width + (1 - kj) * W * .03, y, al * kj); y += im.height * .78


# ------------------------------------------------------------------ 22
@effet('griffonnage', 'Des dessins au feutre se tracent tout seuls autour de toi', alias=('scribble', 'feutre', 'doodle'))
def griffonnage(s, e):
    c = couleur(e.o.get('couleur', e.o.get('color')), OR) + (255,); ep = max(6, s.W // 130)
    calque = vide(s.W, s.H); d = ImageDraw.Draw(calque); rx, ry = s.vt, s.vt * 1.3
    angles = np.linspace(-1.9, -1.9 + 2 * math.pi * 1.08, 70)
    cercle = [(s.vx + rx * (1 + .04 * math.sin(3 * a)) * math.cos(a), s.vy + ry * (1 + .04 * math.cos(2 * a)) * math.sin(a)) for a in angles]
    trace(d, cercle, c, ep, douce(s.t / .5))
    lx, ly = borne(s.vx + s.vt * 2.3, s.W * .2, s.W * .8), max(s.H * .08, s.vy - s.vt * 2.4)
    pts = courbe(lx - s.vt * .3, ly + s.vt * .5, s.vx + rx * .85, s.vy - ry * .75, -.3)
    k2 = sortie((s.t - .45) / .35)
    if k2 > 0: trace(d, pts, c, ep, k2)
    if k2 >= .99: pointe(d, pts, c, ep, s.W * .035)
    for j, (sx, sy) in enumerate(((s.vx - s.vt * 1.9, s.vy - s.vt * 1.2), (s.vx - s.vt * 1.5, s.vy + s.vt * .6), (s.vx + s.vt * 1.6, s.vy + s.vt * .3))):
        r = rebond((s.t - .8 - .1 * j) / .25) * s.vt * .28
        if r > 0: d.line([(sx - r, sy), (sx + r, sy)], fill=c, width=ep); d.line([(sx, sy - r), (sx, sy + r)], fill=c, width=ep)
    al = borne((e.d - s.t) / .2); composer(s, calque, 0, 0, al)
    if s.t > .7:
        lib = mot(e.o.get('texte', 'moi !'), s.W * .075, 'feutre', c[:3], ombre=6)
        poser(s, lib, lx, ly - lib.height * .15, .7 + .3 * rebond((s.t - .7) / .3), 8, al)


# ------------------------------------------------------------------ 24
@effet('collage-rouge', 'Toi en noir et blanc, un mot rouge géant derrière, trois lignes qui claquent', alias=('red-collage', 'collage'))
def collage_rouge(s, e):
    k = entree_sortie(s, e, .15, 0); m = s.masque[..., None]
    nb = etalonner(s.img, 'nb'); s.img = s.img * (1 - k) + (nb * m + nb * .62 * (1 - m)) * k
    assombrir_bords(s, .45 * k)
    r = couleur(e.o.get('couleur', e.o.get('color')), ROUGE); al = borne((e.d - s.t) / .2)
    w = memo(e, 'mot', lambda: mot_ajuste(str(e.o.get('texte', 'MONTAGE')).upper(), s.W * .98, 'ui-gras', 700, fill=r, halo=(r, 34)))
    poser(s, w, s.W / 2, max(w.height * .42, s.vy - s.vt * 1.05), 1.12 - .12 * sortie(s.t / .4), 0, borne(s.t / .12) * al, derriere=True)
    lignes = liste(e.o.get('lignes'), 'UN CLIP.|45 EFFETS.|ZÉRO APPLI.')
    t = memo(e, 'taille', lambda: lignes_ajustees(lignes, s.W * .8, 'ui-gras', int(s.W * .14)))
    y = max(s.H * .5, s.vy + s.vt * 1.55)
    for j, l in enumerate(lignes):
        im = memo(e, ('l', j), lambda: mot(l, t, 'ui-gras', r if j == 1 else BLANC, ombre=8))
        kk = borne((s.t - .18 - .13 * j) / .16)
        if kk > 0: poser(s, im, s.W * .05 + im.width / 2, y + im.height / 2, 1.4 - .4 * sortie(kk), 0, kk * al, protege=True)
        y += t
    tag = memo(e, 'tag', lambda: mot(str(e.o.get('etiquette', 'REC  ·  COLLAGE ROUGE')), s.W * .027, 'mono', r))
    pt = vide(tag.height * .4, tag.height * .4); ImageDraw.Draw(pt).ellipse([0, 0, pt.width - 1, pt.width - 1], fill=r + (255,))
    poser(s, pt, s.W * .07, s.H * .93, alpha=al * k * (1 if int(s.t * 2.5) % 2 == 0 else .35), protege=True)
    poser(s, tag, s.W * .07 + pt.width + tag.width / 2, s.H * .93, alpha=al * k, protege=True)


# ------------------------------------------------------------------ 25
@effet('titre-partage', 'Un bandeau titre descend et te pousse dans la moitié basse de l\'image', alias=('split-headline', 'split', 'bandeau'))
def titre_partage(s, e):
    k = sortie(s.t / .38) * borne((e.d - s.t) / .25); ch = s.H * float(e.o.get('hauteur', .36))
    decaler(s, ch * float(e.o.get('pousse', .72)) * k)
    W = s.W; c = couleur(e.o.get('couleur', e.o.get('color')), BLEU)
    lay = Image.new('RGBA', (W, int(ch)), (244, 242, 236, 255)); d = ImageDraw.Draw(lay)
    lignes = liste(e.o.get('texte'), 'Claude|monte mes|reels.'); fort = e.o.get('fort', e.o.get('hl', 'monte'))
    T = memo(e, 'taille', lambda: lignes_ajustees(lignes, W * .84, 'ui-gras', int(W * .135))); f = police('ui-gras', T)
    for j, l in enumerate(lignes):
        kj = borne((s.t - .12 - .08 * j) / .18)
        if kj <= 0: continue
        y = ch * .13 + j * T * 1.04 + (1 - sortie(kj)) * T * .35; a = int(255 * kj); x = W * .07
        for m_ in l.split(' '):
            fin = '.' if m_.endswith('.') else ''; coeur = m_[:-1] if fin else m_; lw = f.getlength(coeur)
            if coeur == fort:
                hk = sortie((s.t - .42) / .22); p = T * .12
                if hk > 0: d.rounded_rectangle([x - p, y + T * .02, x - p + (lw + 2 * p) * hk, y + T * 1.1], T * .16, fill=c + (a,))
                d.text((x, y), coeur, font=f, fill=(255, 255, 255, a) if hk > .55 else (20, 20, 22, a))
            else: d.text((x, y), coeur, font=f, fill=(20, 20, 22, a))
            x += lw
            if fin: d.text((x, y), fin, font=f, fill=c + (a,)); x += f.getlength(fin)
            x += f.getlength(' ') + (T * .12 if coeur == fort else 0)
    d.rectangle([0, ch - max(5, W // 180), W, ch], fill=c + (255,))
    composer(s, lay, 0, ch * k - ch)
    pt = mot(e.o.get('pastille', e.o.get('pill', 'en quelques secondes ↗')), W * .032, 'ui-gras', BLANC)
    pi = boite(pt.width + W * .02, pt.height * .95, pt.height * .47, c + (255,)); pi.alpha_composite(pt, (int(W * .01), int(-pt.height * .025)))
    poser(s, avec_ombre(pi, 10, 4, 80), W * .93 - pi.width / 2, ch * k + pi.height * .95, .6 + .4 * apparait(s, .62), 0, borne((s.t - .62) / .1) * k, protege=True)


# ------------------------------------------------------------------ 26
_degrades = {}


@effet('mot-pastel', 'Fond lavande, un mot géant derrière toi et une carte de profil qu\'on suit', alias=('pastel-word', 'pastel'))
def mot_pastel(s, e):
    W, H = s.W, s.H; k = entree_sortie(s, e, .2, 0); m = s.masque[..., None]; al = borne((e.d - s.t) / .2)
    if (W, H) not in _degrades:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); t = np.clip(yy / H * .8 + xx / W * .2, 0, 1)[..., None]
        _degrades[(W, H)] = np.float32([.70, .67, .97]) * (1 - t) + np.float32([.93, .90, 1.0]) * t
    lum = (s.img @ np.float32([.299, .587, .114]))[..., None]
    s.img = s.img * (1 - k) + (np.clip(s.img * .93 + .05, 0, 1) * m + _degrades[(W, H)] * (.86 + .22 * lum) * (1 - m)) * k
    grand = memo(e, 'mot', lambda: mot_ajuste(str(e.o.get('texte', 'REELS')).upper(), W * .96, 'ui-gras', 700, fill=BLANC))
    poser(s, avec_ombre(grand, 24, 12, 60), W / 2, max(grand.height * .45, s.vy - s.vt * 1.2) - (1 - sortie(s.t / .45)) * H * .06, 1, 0, al * borne(s.t / .15), derriere=True)
    cw, chh = W * .86, W * .15; cy = H * .865 + (1 - sortie((s.t - .15) / .35)) * H * .2
    carte = boite(cw, chh, chh * .3, (255, 255, 255, 248)); d = ImageDraw.Draw(carte)
    av = pastille_visage(s, e, chh * .64); carte.alpha_composite(av, (int(chh * .18), int((chh - av.height) / 2)))
    violet = (124, 92, 255)
    d.text((chh * .98, chh * .38), e.o.get('nom', 'Idriss Laouali'), font=police('ui-gras', chh * .22), fill=(20, 20, 22, 255), anchor='lm')
    h1 = e.o.get('compte', '@idrisstechinsider  ·  '); f = police('ui', chh * .15)
    d.text((chh * .98, chh * .66), h1, font=f, fill=(140, 140, 150, 255), anchor='lm')
    d.text((chh * .98 + f.getlength(h1), chh * .66), e.o.get('role', 'créateur'), font=f, fill=violet + (255,), anchor='lm')
    a_ = e.d * .6; suivi = s.t >= a_
    d.text((cw - chh * .22, chh / 2), 'Abonné' if suivi else 'Suivre', font=police('ui-gras', chh * .2),
           fill=(140, 140, 150, 255) if suivi else violet + (255,), anchor='rm')
    poser(s, avec_ombre(carte, 18, 8, 90), W / 2, cy, 1 - .06 * math.sin(math.pi * borne((s.t - a_) / .25)) if suivi else 1, 0, al * borne((s.t - .15) / .12), protege=True)
    cu = memo(e, 'curseur', lambda: curseur(W * .06)); ck = douce((s.t - .25) / max(.2, a_ - .3))
    tx, ty = W / 2 + cw / 2 - chh * .55, cy + chh * .12; sx, sy = W * 1.02, H * 1.02
    poser(s, cu, sx + (tx - sx) * ck + cu.width / 2, sy + (ty - sy) * ck + cu.height / 2, .85 if suivi and s.t - a_ < .15 else 1, 0, al * borne((s.t - .25) / .1))


# ------------------------------------------------------------------ 29
@effet('titre-encadre', 'Un zoom avec un titre sur deux lignes, la seconde dans un cadre blanc', alias=('headline-box', 'headline', 'titre'))
def titre_encadre(s, e):
    zoom_visage(s, 1 + (float(e.o.get('zoom', 1.2)) - 1) * sortie(s.t / .22), .45)
    W = s.W; al = borne((e.d - s.t) / .2); lignes = liste(e.o.get('texte'), 'Comment Claude|monte mes reels.')
    T = memo(e, 'taille', lambda: lignes_ajustees(lignes, W * .84, 'ui-gras', int(W * .085)))
    y = max(s.H * .06, s.vy - s.vt * 1.3 - T * 1.3 * len(lignes))
    for j, l in enumerate(lignes):
        kj = borne((s.t - .1 - .12 * j) / .18); encadre = j == len(lignes) - 1
        if kj > 0:
            t = memo(e, ('t', j), lambda: mot(l, T, 'ui-gras', (16, 16, 18) if encadre else BLANC, ombre=0 if encadre else 9))
            if encadre:
                cadre = boite(t.width - T * .15, T * 1.22, T * .08, (255, 255, 255, 255))
                cadre = cadre.crop((0, 0, max(1, int(cadre.width * sortie(kj))), cadre.height))
                composer(s, cadre, W / 2 - (t.width - T * .15) / 2, y, al, protege=True)
            poser(s, t, W / 2, y + T * .6, .92 + .08 * sortie(kj), 0, al * kj, protege=True)
        y += T * 1.3


# ------------------------------------------------------------------ 35
@effet('mur-titres', 'Tes propres titres de reels s\'empilent derrière ta tête, puis ton total de vues apparaît devant', alias=('headline-wall', 'headlines'))
def mur_titres(s, e):
    W, H = s.W, s.H; u = W / 1080; al = borne((e.d - s.t) / .2)
    items = [x.split('::') for x in str(e.o.get('texte', '7 outils IA que personne ne te montre::161K vues|Une IA dans ton téléphone, sans internet::58K vues|'
                                                 'Claude a monté 100 % de cette vidéo::44K vues|5 IA gratuites qui marchent sans internet::39K vues|'
                                                 'Le Niger, 3e puissance de l\'IA ? On vérifie::31K vues|C\'est quoi un modèle d\'IA ?::27K vues|'
                                                 'Pourquoi l\'IA open source est une chance pour l\'Afrique::22K vues')).split('|')]
    looks = [((255, 255, 255), (20, 20, 22)), ((22, 20, 24), (255, 255, 255)), ((246, 238, 226), (30, 24, 20)), (OR, (20, 20, 22)), (BLEU, (255, 255, 255))]
    compte = e.o.get('compte', '@idrisstechinsider')

    def carte(i):
        titre, meta = (items[i % len(items)] + [''])[:2]; fond, ink = looks[i % len(looks)]
        cw = int(W * .5); f = police('ui-gras', cw * .085); lignes, cur = [], ''
        for m_ in titre.split(' '):
            essai = (cur + ' ' + m_).strip()
            if f.getlength(essai) > cw * .84 and cur: lignes.append(cur); cur = m_
            else: cur = essai
        lignes.append(cur); lh = cw * .1; ch = int(cw * .1 + lh * len(lignes) + cw * .16)
        im = boite(cw, ch, cw * .04, fond + (255,)); d = ImageDraw.Draw(im)
        for j, l in enumerate(lignes): d.text((cw * .08, cw * .07 + j * lh), l, font=f, fill=ink + (255,))
        my, t = ch - cw * .085, cw * .04
        d.polygon([(cw * .08, my - t / 2), (cw * .08, my + t / 2), (cw * .08 + t * .9, my)], fill=(255, 48, 64, 255))
        d.text((cw * .08 + t * 1.5, my), f'{compte}  ·  {meta}' if meta else compte, font=police('ui', cw * .045), fill=ink + (170,), anchor='lm')
        return avec_ombre(im, 14, 8, 110)
    N = int(e.o.get('nombre', e.o.get('count', 13)))
    cartes = memo(e, 'cartes', lambda: [carte(i) for i in range(N)])
    pos = memo(e, 'pos', lambda: [(random.Random(i * 7 + 1).uniform(.2, .8), random.Random(i * 7 + 2).uniform(.07, .42), random.Random(i * 7 + 3).uniform(-9, 9)) for i in range(N)])
    pas = float(e.o.get('ecart', .09))
    for i in range(N):
        t0 = i * pas
        if s.t < t0: break
        x, y, r = pos[i]; poser(s, cartes[i], x * W, y * H, .55 + .45 * rebond((s.t - t0) / .22), r, al * borne((s.t - t0) / .06), derriere=True)
    t1 = N * pas + .1
    if s.t > t1:
        a = mot(str(e.o.get('total', '382K')), 96 * u, 'titre', BLANC); b = mot(str(e.o.get('libelle', 'vues sur 7 reels')), 34 * u, 'ui-gras', BLANC)
        pw, ph = int(a.width + b.width + 30 * u), int(max(a.height, b.height) + 10 * u)
        pi = boite(pw, ph, ph * .28, BLEU + (245,)); pi.alpha_composite(a, (int(8 * u), (ph - a.height) // 2)); pi.alpha_composite(b, (int(a.width + 8 * u), (ph - b.height) // 2))
        poser(s, avec_ombre(pi, 18, 8, 110), W / 2, max(s.vy + s.vt * 1.8, H * .6), .6 + .4 * apparait(s, t1, .3), -3, al * borne((s.t - t1) / .08), protege=True)


# ------------------------------------------------------------------ 39
TEXTE_RACCORD = ('un seul clip est entré et chaque coupe est revenue avant midi alors que les monteurs passaient des semaines entières '
                 'à refaire la même timeline à la main les premiers utilisateurs ont trouvé ça troublant puis impossible à ignorer '
                 'les blancs avaient disparu les sous titres tombaient juste et la couleur ressemblait enfin à la pièce où tout avait '
                 'été filmé personne n a ouvert de logiciel de montage de la semaine').split()


def page_journal(s, e, j, wx, wy):
    W, H = s.W, s.H; r = random.Random(31 + j)
    papier = [(246, 243, 236), (236, 229, 212), (251, 251, 250), (241, 236, 228), (232, 232, 230), (248, 240, 228)][j % 6]
    style = ['serif-fin', 'mont', 'ui', 'serif', 'titre', 'texte'][j % 6]
    t = W * [.085, .07, .072, .095, .08, .068][j % 6]; f = police(style, t); lh = t * 1.22
    m_ = str(e.o.get('texte', 'Claude')); rouge = couleur(e.o.get('couleur', e.o.get('color')), (214, 40, 40))
    im = Image.new('RGB', (W, H), papier); d = ImageDraw.Draw(im); encre = (40, 38, 36)
    asc = -f.getbbox('Ag')[1]; ww = f.getlength(m_); bx0 = wx - ww / 2

    def ligne(x, y, sens):
        while x < W + t if sens > 0 else x > -t * 6:
            w_ = r.choice(TEXTE_RACCORD) + ' '
            if sens < 0: x -= f.getlength(w_)
            d.text((x, y), w_, font=f, fill=encre)
            if sens > 0: x += f.getlength(w_)
    dec = r.uniform(0, t * 3); y = wy - asc - lh * math.ceil((wy - asc) / lh + 1)
    while y < H + lh:
        if abs(y - (wy - asc)) >= 1: ligne(-dec - r.uniform(0, t * 4), y, 1)
        y += lh
    ky = wy - asc; d.rectangle([0, ky - lh * .1, W, ky + lh * .95], fill=papier)
    ligne(bx0 - t * .45, ky, -1); ligne(bx0 + ww + t * .45, ky, 1)
    a = np.asarray(im, np.float32) / 255; fl = cv2.GaussianBlur(a, (0, 0), W * .006)
    yy, xx = np.ogrid[0:H, 0:W]; dd = np.clip((((xx - wx) / (W * .62)) ** 2 + ((yy - wy) / (H * .32)) ** 2) - .15, 0, 1)[..., None]
    a = (a * (1 - dd) + fl * dd) * (1 - .18 * np.clip(dd * 1.4, 0, 1))
    pg = Image.fromarray((a * 255).astype(np.uint8)).convert('RGBA')
    bb = f.getbbox(m_); px, py = t * .22, t * .12
    cadre = boite(ww + 2 * px, bb[3] - bb[1] + 2 * py + t * .08, t * .08, rouge + (255,))
    ImageDraw.Draw(cadre).text((px, py - bb[1]), m_, font=f, fill=(255, 255, 255, 255))
    pg.alpha_composite(cadre, (int(bx0 - px), int(wy - asc + bb[1] - py)))
    return np.asarray(pg.convert('RGB'), np.uint8)


@effet('raccord', 'Des pages de journaux défilent en coupant sur un seul mot, figé derrière ta tête', alias=('match-cut', 'match', 'journaux'))
def raccord(s, e):
    k = borne(s.t / .06) * borne((e.d - s.t) / .12)
    zoom_visage(s, 1 + .06 * sortie(s.t / e.d), .44)
    wx, wy = memo(e, 'ancre', lambda: (s.W / 2, max(s.H * .1, s.vy - s.vt * 1.55)))
    durees = [.15, .15, .17, .19, .22, .26, .3, .45]; t, j = s.t, 0
    while j < len(durees) - 1 and t > durees[j]: t -= durees[j]; j += 1
    pg = memo(e, ('page', j), lambda: page_journal(s, e, j, wx, wy)).astype(np.float32) / 255
    m = s.masque[..., None]; s.img = s.img * (1 - k) + (pg * (1 - m) + s.img * m) * k


# ------------------------------------------------------------------ 41
@effet('enseigne', 'La lumière baisse et une enseigne LED s\'écrit derrière toi', alias=('led-sign', 'led', 'neon'))
def enseigne(s, e):
    k = entree_sortie(s, e, .2, .2)
    zoom_visage(s, 1 + (float(e.o.get('pousse', 1.08)) - 1) * douce(s.t / e.d), .42)
    lignes = str(e.o.get('texte', 'KARATOU')).upper().split('|'); c = np.float32(couleur(e.o.get('couleur', e.o.get('color')), OR)) / 255

    def prepare():
        mats = []
        for l in lignes:
            f = police('ui-gras', 40); w = int(f.getlength(l)) + 8
            im = Image.new('L', (w, 56), 0); ImageDraw.Draw(im).text((4, 2), l, font=f, fill=255); im = im.crop(im.getbbox() or (0, 0, w, 56))
            cols = max(1, round(im.width / im.height * 11)); mats.append(np.asarray(im.resize((cols, 11), Image.BOX), np.float32) / 255 > .42)
        cols = max(m.shape[1] for m in mats) + 2; cel = int(min(s.W * .96 / cols, s.H * .3 / (len(mats) * 12)))
        L = np.zeros((len(mats) * 12 - 1, cols), np.float32)
        for i, m in enumerate(mats): o = (cols - m.shape[1]) // 2; L[i * 12:i * 12 + 11, o:o + m.shape[1]] = m
        yy, xx = np.mgrid[0:cel, 0:cel].astype(np.float32)
        return L, cel, np.clip(cel * .36 - np.hypot(xx - cel / 2 + .5, yy - cel / 2 + .5) + .5, 0, 1), np.random.default_rng(3).random(L.shape).astype(np.float32)
    L, cel, point, alea = memo(e, 'matrice', prepare); rows, cols = L.shape
    allume = L * np.clip((borne((s.t - .15) / .75) * (cols + 4) - np.arange(cols)[None, :]) / 3, 0, 1)
    b = np.maximum(allume * (.82 + .18 * np.sin(alea * 50 + s.t * 30)), .09)
    pan = np.kron(b, point)[..., None] * c; pan = np.clip(pan + cv2.GaussianBlur(pan, (0, 0), cel * .9) * 1.6, 0, 1)
    ph, pw = pan.shape[:2]; x0 = int(s.W / 2 - pw / 2); y0 = int(max(s.H * .03, s.vy - s.vt * .75 - ph))
    xx, yy = grille(s); d = ((xx - s.vx) / (s.W * .6)) ** 2 + ((yy - (s.vy + s.H * .25)) / (s.H * .55)) ** 2
    s.img *= ((1 - k * (.84 - .3 * np.clip(1 - d, 0, 1))) * (1 - s.masque) + s.masque * (1 - .18 * k))[..., None]
    xa, xb, ya, yb = max(0, x0), min(s.W, x0 + pw), max(0, y0), min(s.H, y0 + ph)
    if xb > xa and yb > ya:
        s.img[ya:yb, xa:xb] = np.clip(s.img[ya:yb, xa:xb] + pan[ya - y0:yb - y0, xa - x0:xb - x0] * k * (1 - s.masque[ya:yb, xa:xb, None]), 0, 1)


# ------------------------------------------------------------------ 31
@effet('classement', 'Un classement S à F tombe devant toi et Claude file tout en haut', alias=('tier-list', 'tiers', 'tier'))
def classement(s, e):
    W, H = s.W, s.H; al = borne((e.d - s.t) / .2)
    titre = memo(e, 'titre', lambda: mot_ajuste(str(e.o.get('titre', 'meilleure façon de monter un reel ?')), W * .88, 'italique', int(W * .11), fill=OR, ombre=8))
    poser(s, titre, W / 2, max(titre.height * .6, s.vy - s.vt * 1.65), .9 + .1 * sortie(s.t / .3), 0, al * borne(s.t / .15), derriere=True)
    rangs = [('S', (255, 127, 127)), ('A', (255, 191, 127)), ('B', (255, 223, 127)), ('C', (191, 255, 127)), ('D', (127, 191, 255)), ('F', (191, 127, 255))]
    cw, rh, m = int(W * .66), int(W * .082), int(W * .015); ch = m * 2 + rh * 6 + m * 5
    autres = dict(zip('BCDF', liste(e.o.get('autres'), 'modèles|timelines|applis|tout à la main')))

    def tableau():
        im = boite(cw, ch, W * .025, (22, 22, 26, 240)); d = ImageDraw.Draw(im)
        for i, (lettre, c) in enumerate(rangs):
            y = m + i * (rh + m)
            d.rounded_rectangle([m, y, m + rh, y + rh], rh * .14, fill=c + (255,))
            d.text((m + rh / 2, y + rh / 2), lettre, font=police('ui-gras', rh * .5), fill=(20, 20, 22, 255), anchor='mm')
            d.rounded_rectangle([m * 2 + rh, y, cw - m, y + rh], rh * .14, fill=(40, 40, 46, 255))
            if lettre in autres:
                f = police('ui', rh * .3); tw = f.getlength(autres[lettre]) + rh * .4
                d.rounded_rectangle([m * 3 + rh, y + rh * .15, m * 3 + rh + tw, y + rh * .85], rh * .12, fill=(78, 78, 86, 255))
                d.text((m * 3 + rh + rh * .2, y + rh / 2), autres[lettre], font=f, fill=(225, 225, 230, 255), anchor='lm')
        return avec_ombre(im, 18, 10, 120)
    tb = memo(e, 'tableau', tableau)
    haut = min(H * .95 - tb.height, max(s.vy + s.vt * 1.4, H * .45)); bx, by = W / 2, haut + tb.height / 2 + (1 - rebond(s.t / .35)) * H * .15
    poser(s, tb, bx, by, 1, 0, al * borne(s.t / .12), protege=True)
    tuile = memo(e, 'tuile', lambda: avec_ombre(boite(int(rh * 2.6), int(rh * .8), rh * .16, CLAUDE + (255,)), 8, 4, 100))
    tx = memo(e, 'tx', lambda: mot(str(e.o.get('element', 'Claude')), rh * .36, 'ui-gras', BLANC))
    t = tuile.copy(); t.alpha_composite(tx, ((t.width - tx.width) // 2, (t.height - tx.height) // 2 - 3))
    sx, sy = W * .86, s.vy + s.vt * .4
    ex, ey = bx - tb.width / 2 + 18 + m * 3 + rh + tuile.width / 2 - 10, by - tb.height / 2 + 18 + m + rh / 2
    q = rebond((s.t - .45) / .4)
    if s.t > .4: poser(s, t, sx + (ex - sx) * q, sy + (ey - sy) * q, 1.25 - .25 * borne(q), 18 * (1 - borne(q)), al, protege=True)


# ------------------------------------------------------------------ 11
@effet('a-faire', 'Une liste à faire à côté de ta tête, cochée au fil de tes mots', alias=('todo', 'to-do', 'liste'))
def a_faire(s, e):
    items = liste(e.o.get('texte'), 'glisse ta vidéo dans Claude|installe la skill|tape /effets')
    moments = [float(t) - e.debut for t in str(e.o.get('moments', e.o.get('ticks'))).split('|')] if e.o.get('moments', e.o.get('ticks')) else [e.d * (i + 1) / (len(items) + 1) for i in range(len(items))]
    cw = int(s.W * .5); lh, m = int(cw * .13), int(cw * .07)
    im = boite(cw, m * 2 + lh * (len(items) + 1), cw * .07, (250, 248, 242, 235)); d = ImageDraw.Draw(im)
    d.text((m, m), str(e.o.get('titre', 'À FAIRE')).upper(), font=police('ui', lh * .42), fill=(200, 140, 20, 255))
    d.text((cw - m, m), f'{sum(s.t >= t for t in moments)} sur {len(items)}', font=police('ui', lh * .36), fill=(120, 120, 120, 255), anchor='ra')
    f = police('ui', lh * .4)
    for i, it in enumerate(items):
        y = m + lh * (i + 1); bx = lh * .42
        d.rounded_rectangle([m, y + lh * .12, m + bx, y + lh * .12 + bx], 6, outline=(160, 160, 160, 255), width=3)
        d.text((m + bx * 1.5, y + lh * .1), it, font=f, fill=ENCRE + (255,))
        if s.t >= moments[i]:
            k = sortie((s.t - moments[i]) / .25)
            d.rounded_rectangle([m, y + lh * .12, m + bx, y + lh * .12 + bx], 6, fill=(52, 199, 89, 255))
            coche(d, m + bx * .18, y + lh * .12 + bx * .2, bx * .64, ep=4)
            d.line([(m + bx * 1.5, y + lh * .36), (m + bx * 1.5 + f.getlength(it) * k, y + lh * .36)], fill=ENCRE + (255,), width=3)
    x = s.W * .05 + cw / 2 if s.vx > s.W / 2 else s.W * .95 - cw / 2
    poser(s, avec_ombre(im, 14, 8, 90), x, max(im.height / 2 + s.H * .06, s.vy - s.vt * 1.4), .8 + .2 * rebond(s.t / .3), 0,
          borne(s.t / .12) * borne((e.d - s.t) / .2), derriere=True)


# ------------------------------------------------------------------ 2
NOMS = ['Avalanche', 'Alignement', 'Verrouillé', 'Orbite', 'Plongée', 'Mot géant', 'Projecteur', 'Ticket', 'Ambiance', 'Avant / après',
        'À faire', 'Commentaire', 'Abonnement', 'Pause flèche', 'Désinstallation', 'Cadre reel', 'Pluie de touches', 'Tampon',
        'Compte à rebours', 'Tunnel', 'Couverture', 'Griffonnage']


@effet('alignement', 'Des tuiles numérotées s\'ouvrent en éventail au-dessus de ta tête', alias=('lineup', 'the-lineup', 'eventail'))
def alignement(s, e):
    noms = liste(e.o.get('texte'), '|'.join(NOMS)); tw = int(s.W * .105)

    def tuile(i, nom):
        im = boite(tw, tw * 1.25, tw * .16, (24, 24, 28, 225), (255, 255, 255, 60), 2); d = ImageDraw.Draw(im)
        n = mot(f'{i + 1:02d}', tw * .42, 'italique', OR); im.alpha_composite(n, ((tw - n.width) // 2, int(tw * .04)))
        mm = nom.split(' '); lignes = [' '.join(mm[:len(mm) // 2 or 1]), ' '.join(mm[len(mm) // 2 or 1:])] if len(nom) > 10 else [nom]
        for j, l in enumerate([l for l in lignes if l]):
            d.text((tw / 2, tw * (.78 + .19 * j)), l, font=police('ui', tw * .14), fill=(255, 255, 255, 235), anchor='mm')
        return avec_ombre(im, 8, 5, 90)
    tuiles = memo(e, 'tuiles', lambda: [tuile(i, n) for i, n in enumerate(noms)])
    n = len(tuiles); ext = math.ceil(n / 2 + .5); cx, cy = s.W / 2 * .6 + s.vx * .4, s.vy + s.vt * .3; places = []
    for nb, R in ((ext, s.W * .47), (n - ext, s.W * .33)):
        for k in range(nb):
            a = math.pi * (.94 - .88 * k / max(1, nb - 1))
            places.append((cx + R * math.cos(a), cy - R * math.sin(a) * 1.05, math.degrees(a - math.pi / 2) * .3))
    fin = borne((e.d - s.t) / .2)
    for i, (x, y, r) in enumerate(places[:n]):
        t0 = .035 * i
        if s.t < t0: continue
        k = rebond((s.t - t0) / .3)
        poser(s, tuiles[i], x, y + (1 - k) * 40, .5 + .5 * k, r, borne((s.t - t0) / .1) * fin, derriere=True)
