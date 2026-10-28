"""Les effets d'interface : commentaire Instagram, bouton S'abonner, timeline de montage."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import effet
from .base import (borne, sortie, douce, rebond, couleur, police, mot, mot_ajuste, boite, avec_ombre, composer, poser, assombrir_bords,
                   entree_sortie, memo, vide, ENCRE, OR, BLEU, CLAUDE)
from .camera import coeur
from .verre import pastille_visage

BLANC = (255, 255, 255)


# ------------------------------------------------------------------ 12
def barre_commentaire(s, e):
    txt = str(e.o.get('texte', 'EFFETS')); bw, bh = int(s.W * .9), int(s.W * .11)
    y = s.H * .8 + (1 - sortie(s.t / .3)) * s.H * .25; t_post = .35 + .08 * len(txt) + .25
    tape = txt[:int(borne((s.t - .35) / (.08 * len(txt))) * len(txt) + .001)] if s.t < t_post else ''
    im = boite(bw, bh, bh / 2, (255, 255, 255, 245)); d = ImageDraw.Draw(im); r = bh * .32
    d.ellipse([bh * .2, bh / 2 - r, bh * .2 + 2 * r, bh / 2 + r], fill=(214, 41, 118, 255)); f = police('ui', bh * .3)
    if tape: d.text((bh * .95, bh / 2), tape + ('|' if int(s.t * 4) % 2 else ''), font=f, fill=ENCRE + (255,), anchor='lm')
    elif s.t < t_post: d.text((bh * .95, bh / 2), 'Ajoute un commentaire...', font=f, fill=(150, 150, 150, 255), anchor='lm')
    d.text((bw - bh * .4, bh / 2), 'Publier', font=f, fill=(0, 149, 246, 255) if tape else (180, 210, 240, 255), anchor='rm')
    al = borne((e.d - s.t) / .2); poser(s, avec_ombre(im, 14, 6, 100), s.W / 2, y, alpha=al, protege=True)
    if s.t >= t_post:
        k = rebond((s.t - t_post) / .3); b = boite(int(s.W * .52), int(bh * .85), bh * .3, (255, 255, 255, 240)); bd = ImageDraw.Draw(b)
        bd.text((bh * .3, b.height * .32), 'toi', font=police('ui', bh * .2), fill=(120, 120, 120, 255), anchor='lm')
        bd.text((bh * .3, b.height * .66), txt, font=police('ui', bh * .3), fill=ENCRE + (255,), anchor='lm')
        hk = rebond((s.t - t_post - .3) / .3)
        if hk > 0: h = coeur(bh * .4 * hk); b.alpha_composite(h, (int(b.width - bh * .3 - h.width), int(b.height / 2 - h.height / 2)))
        poser(s, avec_ombre(b, 12, 5, 90), s.W * .07 + b.width / 2, y - bh * 1.05, .7 + .3 * k, 0, al * borne((s.t - t_post) / .1), protege=True)


@effet('commentaire', 'Une fenêtre de commentaires Instagram au-dessus de ta tête : ton mot s\'écrit, se publie, reçoit un cœur et ta réponse (look=barre pour la version simple)',
       alias=('comment-box', 'comment', 'commentaires'))
def commentaire(s, e):
    if e.o.get('look') in ('barre', 'bar'): return barre_commentaire(s, e)
    W, H = s.W, s.H; u = W / 1080; al = borne((e.d - s.t) / .2)
    txt = str(e.o.get('texte', 'EFFETS')); compte = e.o.get('compte', 'idrisstechinsider')
    reponse = e.o.get('reponse', 'Je t\'envoie le pack 🎁'); puce = e.o.get('puce', '45 effets')
    sw, sh = 740 * u, 450 * u; t_post = .3 + .06 * len(txt) + .1; t_coeur, t_rep = t_post + .25, t_post + .4
    feuille = boite(sw, sh, 30 * u, (38, 38, 40, 248)); d = ImageDraw.Draw(feuille)
    blanc, gris = (245, 245, 245, 255), (160, 160, 166, 255)
    d.rounded_rectangle([sw / 2 - 32 * u, 14 * u, sw / 2 + 32 * u, 20 * u], 3 * u, fill=(110, 110, 116, 255))
    d.text((sw / 2, 50 * u), 'Commentaires', font=police('ui-gras', 26 * u), fill=blanc, anchor='mm')
    d.line([(0, 80 * u), (sw, 80 * u)], fill=(60, 60, 64, 255), width=max(1, int(2 * u)))

    def avatar(t, lettre='T', c=(233, 90, 140)):
        a = vide(t, t); ad = ImageDraw.Draw(a); ad.ellipse([0, 0, t - 1, t - 1], fill=c + (255,))
        ad.text((t / 2, t / 2), lettre, font=police('ui-gras', t * .5), fill=(255, 255, 255, 255), anchor='mm'); return a
    if s.t < t_post:
        d.text((sw / 2, 190 * u), 'Lance la conversation.', font=police('ui', 21 * u), fill=gris, anchor='mm')
    else:
        q = sortie((s.t - t_post) / .25); oy = (1 - q) * -20 * u; a8 = int(255 * borne(q * 1.5))
        av = avatar(int(46 * u)); av.putalpha(av.split()[3].point(lambda v: v * a8 // 255)); feuille.alpha_composite(av, (int(26 * u), int(100 * u + oy)))
        d.text((88 * u, 108 * u + oy), 'toi', font=police('ui-gras', 19 * u), fill=blanc[:3] + (a8,), anchor='lm')
        d.text((88 * u + police('ui-gras', 19 * u).getlength('toi ') + 4 * u, 108 * u + oy), 'maintenant', font=police('ui', 18 * u), fill=gris[:3] + (a8,), anchor='lm')
        d.text((86 * u, 128 * u + oy), txt, font=police('ui-gras', 50 * u), fill=blanc[:3] + (a8,))
        d.text((88 * u, 196 * u + oy), 'Répondre', font=police('ui', 17 * u), fill=gris[:3] + (a8,), anchor='lm')
        hk = rebond((s.t - t_coeur) / .3)
        if hk > 0: h = coeur(30 * u * hk); feuille.alpha_composite(h, (int(sw - 46 * u - h.width / 2), int(130 * u - h.height / 2)))
        rk = sortie((s.t - t_rep) / .25)
        if rk > 0:
            ra = int(255 * borne(rk * 1.5)); ry = 226 * u + (1 - rk) * 16 * u; rx = 88 * u
            pv = pastille_visage(s, e, 34 * u); pv.putalpha(pv.split()[3].point(lambda v: v * ra // 255)); feuille.alpha_composite(pv, (int(rx), int(ry)))
            d.text((rx + 46 * u, ry + 8 * u), compte, font=police('ui-gras', 18 * u), fill=blanc[:3] + (ra,), anchor='lm')
            d.text((rx + 46 * u + police('ui-gras', 18 * u).getlength(compte) + 10 * u, ry + 8 * u), 'Auteur', font=police('ui', 16 * u), fill=gris[:3] + (ra,), anchor='lm')
            d.text((rx + 46 * u, ry + 36 * u), reponse.replace('🎁', '').strip(), font=police('ui', 22 * u), fill=blanc[:3] + (ra,), anchor='lm')
            ck = rebond((s.t - t_rep - .12) / .3)
            if ck > 0:
                ct = mot('🔗 ' + puce if False else puce, 19 * u, 'ui-gras', (20, 20, 22))
                cp = boite(ct.width + 10 * u, ct.height * .9, ct.height * .45, OR + (255,)); cp.alpha_composite(ct, (int(5 * u), int((cp.height - ct.height) / 2)))
                cp = cp.resize((max(1, int(cp.width * (.6 + .4 * ck))), max(1, int(cp.height * (.6 + .4 * ck)))))
                feuille.alpha_composite(cp, (int(rx + 46 * u), int(ry + 56 * u)))
    iy = sh - 78 * u
    feuille.alpha_composite(avatar(int(48 * u)), (int(22 * u), int(iy)))
    d.rounded_rectangle([82 * u, iy, sw - 22 * u, iy + 48 * u], 24 * u, fill=(54, 54, 58, 255))
    for j, c in enumerate(((255, 59, 48), (255, 204, 0), (255, 149, 0), (52, 199, 89), (0, 122, 255), (175, 82, 222))):   # réactions
        cx = 52 * u + j * 56 * u; d.ellipse([cx - 16 * u, sh - 140 * u, cx + 16 * u, sh - 108 * u], fill=c + (230,))
    tape = txt[:int(borne((s.t - .3) / (.06 * len(txt))) * len(txt) + 1e-3)] if s.t < t_post else ''
    if tape:
        d.text((104 * u, iy + 24 * u), tape, font=police('ui-gras', 26 * u), fill=blanc, anchor='lm')
        if int(s.t * 4) % 2:
            x = 104 * u + police('ui-gras', 26 * u).getlength(tape) + 3 * u; d.rectangle([x, iy + 10 * u, x + 2 * u, iy + 38 * u], fill=(0, 149, 246, 255))
    else:
        d.text((104 * u, iy + 24 * u), f'Commente pour {compte}', font=police('ui', 20 * u), fill=gris, anchor='lm')
    appuye = t_post - .08 <= s.t < t_post
    d.text((sw - 44 * u, iy + 24 * u), 'Publier', font=police('ui-gras', 23 * u),
           fill=(140, 200, 255, 255) if appuye else ((0, 149, 246, 255) if tape else (70, 110, 160, 255)), anchor='rm')
    feuille = avec_ombre(feuille, 22, 10, 120)
    bas = s.vy - s.vt * .5; ech = max(.6, (bas - H * .02) / feuille.height) if bas - feuille.height < H * .02 else 1.0
    poser(s, feuille, W / 2 * .5 + s.vx * .5, bas - feuille.height * ech / 2 + 3 * u * math.sin(s.t * 3.2), ech * (.85 + .15 * rebond(s.t / .3)), 1.2,
          al * borne(s.t / .1), derriere=True)


# ------------------------------------------------------------------ 13
@effet('abonnement', 'Un bouton « S\'abonner » apparaît et passe à « Abonné »', alias=('tap', 'the-tap', 'follow', 'suivre'))
def abonnement(s, e):
    a_ = float(e.o['a']) - e.debut if 'a' in e.o else (float(e.o['at']) - e.debut if 'at' in e.o else e.d * .45)
    bw, bh = int(s.W * .3), int(s.W * .09)
    x = borne(float(e.o['x']) * s.W if 'x' in e.o else s.vx + s.vt * 1.9, bw / 2 + 30, s.W - bw / 2 - 30)
    y = borne(float(e.o['y']) * s.H if 'y' in e.o else s.vy + s.vt * 1.6, bh + 30, s.H - bh - 30)
    fait = s.t >= a_; c = couleur(e.o.get('couleur', e.o.get('color')), OR) if fait else BLEU
    im = boite(bw, bh, bh * .28, c + (255,))
    ImageDraw.Draw(im).text((bw / 2, bh / 2), 'Abonné ✓' if fait else '+ S\'abonner', font=police('ui-gras', bh * .36), fill=(255, 255, 255, 255), anchor='mm')
    serre = 1 - .12 * math.sin(math.pi * borne((s.t - a_) / .3)) if fait and s.t - a_ < .3 else 1
    poser(s, avec_ombre(im, 12, 6, 110), x, y, (.6 + .4 * rebond(s.t / .3)) * serre, 0, borne(s.t / .1) * borne((e.d - s.t) / .2), protege=True)
    if fait and s.t - a_ < .4:
        q = (s.t - a_) / .4; r = int(bh * (.3 + .9 * q)); an = vide(2 * r + 8, 2 * r + 8)
        ImageDraw.Draw(an).ellipse([4, 4, 2 * r + 4, 2 * r + 4], outline=(255, 255, 255, int(220 * (1 - q))), width=5); poser(s, an, x, y, protege=True)


# ------------------------------------------------------------------ 28
@effet('timeline', 'Un look cinéma rouge sombre avec une timeline de montage, un compteur REC et une tête de lecture lumineuse',
       alias=('auto-edit', 'montage', 'timeline-rouge'))
def timeline(s, e):
    W, H = s.W, s.H; k = entree_sortie(s, e, .2, 0); m = s.masque[..., None]; al = borne((e.d - s.t) / .2)
    lum = (s.img @ np.float32([.299, .587, .114]))[..., None]
    fond = np.clip(lum * np.float32([1.05, .3, .27]) * .85, 0, 1); toi = np.clip(s.img * np.float32([1.04, .86, .82]), 0, 1)
    s.img = s.img * (1 - k) + (toi * m + fond * (1 - m)) * k; assombrir_bords(s, .5 * k)
    r = couleur(e.o.get('couleur', e.o.get('color')), (255, 52, 44)); gl = (1 - sortie(s.t / .35)) * W * .08; tb = borne(s.t / .15) * al
    rec = mot(f"REC 00:{21 + int(s.t * 3):02d}", W * .032, 'mono', r)
    pt = vide(rec.height * .36, rec.height * .36); ImageDraw.Draw(pt).ellipse([0, 0, pt.width - 1, pt.width - 1], fill=r + (255,))
    composer(s, pt, W * .065 - gl, H * .075 + (rec.height - pt.height) / 2, tb * (1 if int(s.t * 2.5) % 2 == 0 else .35), protege=True)
    composer(s, rec, W * .065 + pt.width * 1.4 - gl, H * .075, tb, protege=True)
    ti = memo(e, 'titre', lambda: mot_ajuste(str(e.o.get('texte', 'MONTAGE AUTO')), W * .74, 'ui-gras', int(W * .12), fill=BLANC, ombre=10))
    composer(s, ti, W * .055 - gl, H * .075 + rec.height * .85, tb, protege=True)
    so = memo(e, 'sous', lambda: mot(str(e.o.get('sous', 'timeline par Claude')), W * .037, 'ui', r))
    composer(s, so, W * .065 - gl, H * .075 + rec.height * .85 + ti.height * .88, tb, protege=True)
    pw, ph = int(W * .9), int(H * .19); py = H * .755 + (1 - sortie((s.t - .1) / .35)) * H * .3
    lay = boite(pw, ph, W * .03, (14, 10, 10, 215), (255, 70, 60, 90), 2); d = ImageDraw.Draw(lay)
    for j in range(4): d.text((pw * (.05 + .3 * j), ph * .12), f'00:0{j}', font=police('mono', W * .022), fill=(170, 170, 175, 255), anchor='lm')
    clips = [(rg, a, b) for rg, segs in enumerate([[(.04, .24), (.26, .5), (.53, .76), (.79, .96)], [(.04, .3), (.33, .45), (.48, .7)], [(.04, .55), (.6, .96)]]) for a, b in segs]
    tx = pw * (.04 + .92 * borne(s.t / (e.d * .95))); halo = vide(pw, ph); hd = ImageDraw.Draw(halo)
    for rg, a, b in clips:
        y0 = ph * (.27 + .235 * rg); x0, x1 = pw * a, pw * b; lu = x0 < tx
        d.rounded_rectangle([x0, y0, x1, y0 + ph * .17], ph * .04, fill=r + (255,) if lu else (120, 30, 28, 255))
        if lu: hd.rounded_rectangle([x0, y0, x1, y0 + ph * .17], ph * .04, fill=r + (200,))
    d.line([(tx, ph * .2), (tx, ph * .97)], fill=(255, 255, 255, 255), width=max(3, W // 300))
    hd.line([(tx, ph * .2), (tx, ph * .97)], fill=(255, 255, 255, 255), width=max(8, W // 100))
    composer(s, Image.alpha_composite(halo.filter(ImageFilter.GaussianBlur(W // 90)), lay), (W - pw) / 2, py, al, protege=True)


# ------------------------------------------------------------------ bonus Karatou
def _paquets(mots, n):
    out, cur = [], []
    for m in mots:
        cur.append(m)
        if len(cur) >= n or str(m['mot']).rstrip()[-1:] in '.!?,:': out.append(cur); cur = []
    if cur: out.append(cur)
    return out


@effet('sous-titres', 'Bonus : sous-titres mot par mot en français, le mot prononcé s\'allume en or (mots=fichier de transcrire.py)',
       alias=('captions', 'karaoke', 'soustitres'))
def sous_titres(s, e):
    import json, os
    def charger():
        f = e.o.get('mots', e.o.get('words'))
        if not f or not os.path.exists(str(f)): return []
        d = json.load(open(f)); d = d.get('mots', d.get('words', d)) if isinstance(d, dict) else d
        return _paquets([{'mot': str(m.get('mot', m.get('word', ''))).strip(), 'debut': float(m.get('debut', m.get('start', 0))),
                          'fin': float(m.get('fin', m.get('end', 0)))} for m in d if str(m.get('mot', m.get('word', ''))).strip()],
                        int(e.o.get('paquet', 3)))
    paquets = memo(e, 'paquets', charger); t = s.temps
    actuel = next((p for p in paquets if p[0]['debut'] - .05 <= t < p[-1]['fin'] + .15), None)
    if not actuel: return
    W, H = s.W, s.H; T = int(W * float(e.o.get('taille', .085))); vif = couleur(e.o.get('couleur'), OR)
    maj = str(e.o.get('casse', 'maj')) == 'maj'; f = police('noir', T); esp = f.getlength(' ')
    textes = [m['mot'].upper() if maj else m['mot'] for m in actuel]; larg = [f.getlength(x) for x in textes]
    while sum(larg) + esp * (len(larg) - 1) > W * .9 and T > 20:
        T = int(T * .92); f = police('noir', T); esp = f.getlength(' '); larg = [f.getlength(x) for x in textes]
    x = (W - (sum(larg) + esp * (len(larg) - 1))) / 2; y = H * float(e.o.get('y', .74))
    k = sortie((t - actuel[0]['debut'] + .05) / .12)
    for m, tx, lw in zip(actuel, textes, larg):
        dit = m['debut'] <= t
        im = mot(tx, T, 'noir', vif if dit and t < m['fin'] + .1 else BLANC, contour=max(3, T // 11), ombre=8)
        ech = .85 + .15 * k
        poser(s, im, x + lw / 2, y, ech, 0, borne(k * 2), protege=True); x += lw + esp
