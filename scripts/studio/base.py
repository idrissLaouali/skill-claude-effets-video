"""Briques communes : la scène (une image en cours de montage), les courbes d'animation,
le texte, les cartes, la composition devant ou derrière la personne, et la caméra virtuelle.

Convention : toutes les images de travail sont des tableaux numpy float32, valeurs de 0 à 1.
"""
import math, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------- palette Karatou
BLEU, NUIT, OR = (26, 115, 232), (10, 22, 40), (245, 166, 35)
CREME, ENCRE, ROUGE, VERT = (246, 241, 232), (20, 22, 28), (229, 50, 45), (34, 197, 94)
CLAUDE = (217, 119, 87)

# ---------------------------------------------------------------- polices
_POLICES = {
    'titre': ('Anton-Regular.ttf', None), 'impact': ('ArchivoBlack-Regular.ttf', None),
    'serif': ('PlayfairDisplay.ttf', (800,)), 'serif-fin': ('PlayfairDisplay.ttf', (500,)),
    'italique': ('PlayfairDisplay-Italic.ttf', (600,)), 'elegant': ('InstrumentSerif-Italic.ttf', None),
    'texte': ('dm-sans-latin-500-normal.woff', None), 'gras': ('dm-sans-latin-700-normal.woff', None),
    'noir': ('dm-sans-latin-800-normal.woff', None), 'ui': ('Inter.ttf', (24, 600)), 'ui-gras': ('Inter.ttf', (32, 850)),
    'mono': ('SpaceMono-Bold.ttf', None), 'feutre': ('PermanentMarker-Regular.ttf', None), 'mont': ('Montserrat.ttf', (800,)),
}
_cache_polices = {}


def police(nom, taille):
    cle = (nom, int(taille))
    if cle not in _cache_polices:
        fichier, axes = _POLICES.get(nom, _POLICES['gras'])
        f = ImageFont.truetype(os.path.join(RACINE, 'polices', fichier), max(6, int(taille)))
        if axes:
            try: f.set_variation_by_axes(list(axes))
            except Exception: pass
        _cache_polices[cle] = f
    return _cache_polices[cle]


# ---------------------------------------------------------------- temps et courbes
def borne(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def sortie(x):        # démarre vite, se pose en douceur
    x = borne(x); return 1 - (1 - x) ** 3


def douce(x):         # lent, rapide, lent
    x = borne(x); return x * x * (3 - 2 * x)


def rebond(x, k=1.7):  # dépasse un peu puis revient
    x = borne(x) - 1; return 1 + x * x * ((k + 1) * x + k)


def couleur(v, defaut):
    if v is None or v == '': return defaut
    if isinstance(v, (tuple, list)): return tuple(int(c) for c in v[:3])
    v = str(v).strip().lstrip('#')
    if len(v) == 3: v = ''.join(c * 2 for c in v)
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def liste(v, defaut):
    """Les options multiples s'écrivent avec des barres : 'a|b|c'."""
    if v is None or v == '': v = defaut
    return [x.strip() for x in str(v).split('|')]


# ---------------------------------------------------------------- dessin PIL
def vide(w, h):
    return Image.new('RGBA', (max(1, int(w)), max(1, int(h))), (0, 0, 0, 0))


def mot(txt, taille, style='gras', fill=(255, 255, 255), contour=0, couleur_contour=ENCRE, ombre=0, halo=None):
    """Rend un texte sur fond transparent, recadré au plus près."""
    f = police(style, taille)
    x0, y0, x1, y1 = f.getbbox(txt, stroke_width=contour)
    marge = int(taille * 0.18 + ombre * 3 + (halo[1] * 3 if halo else 0)) + 4
    im = vide(x1 - x0 + 2 * marge, y1 - y0 + 2 * marge)
    pos = (marge - x0, marge - y0)
    if ombre:
        o = vide(*im.size)
        ImageDraw.Draw(o).text((pos[0], pos[1] + ombre * 0.6), txt, font=f, fill=(0, 0, 0, 170), stroke_width=contour)
        im = Image.alpha_composite(im, o.filter(ImageFilter.GaussianBlur(ombre)))
    if halo:
        g = vide(*im.size)
        ImageDraw.Draw(g).text(pos, txt, font=f, fill=tuple(halo[0]) + (255,), stroke_width=max(1, int(taille * 0.035)))
        g = g.filter(ImageFilter.GaussianBlur(halo[1]))
        im = Image.alpha_composite(Image.alpha_composite(im, g), g)
    ImageDraw.Draw(im).text(pos, txt, font=f, fill=tuple(fill) + (255,), stroke_width=contour,
                            stroke_fill=tuple(couleur_contour) + (255,))
    return im


def mot_ajuste(txt, largeur_max, style='titre', depart=420, **kw):
    t = depart
    while t > 10 and police(style, t).getlength(txt) > largeur_max: t = int(t * 0.93)
    return mot(txt, t, style, **kw)


def lignes_ajustees(lignes, largeur_max, style, depart):
    t = depart
    while t > 10 and max(police(style, t).getlength(l) for l in lignes) > largeur_max: t = int(t * 0.93)
    return t


def boite(w, h, r, fill, contour=None, epaisseur=0):
    im = vide(w, h)
    ImageDraw.Draw(im).rounded_rectangle([0, 0, int(w) - 1, int(h) - 1], int(r), fill=fill, outline=contour, width=epaisseur)
    return im


def avec_ombre(im, flou=18, dy=10, force=130):
    m = flou * 2 + abs(dy)
    out = vide(im.width + 2 * m, im.height + 2 * m)
    noir = Image.new('RGBA', im.size, (0, 0, 0, 255)); noir.putalpha(im.split()[3].point(lambda v: v * force // 255))
    out.paste(noir, (m, m + dy), noir)
    out = out.filter(ImageFilter.GaussianBlur(flou)); out.alpha_composite(im, (m, m))
    return out


def vignette_reel(src, largeur, rayon=0.07, ombre=True):
    """Une carte au format reel (9:16), coins arrondis, ombre douce."""
    h = int(largeur * 16 / 9)
    s = src.convert('RGB'); k = max(largeur / s.width, h / s.height)
    s = s.resize((max(largeur, int(s.width * k) + 1), max(h, int(s.height * k) + 1)), Image.LANCZOS)
    g, t = (s.width - largeur) // 2, (s.height - h) // 2
    s = s.crop((g, t, g + largeur, t + h)).convert('RGBA')
    masque = Image.new('L', (largeur, h), 0)
    ImageDraw.Draw(masque).rounded_rectangle([0, 0, largeur - 1, h - 1], int(largeur * rayon), fill=255)
    s.putalpha(masque)
    ImageDraw.Draw(s).rounded_rectangle([0, 0, largeur - 1, h - 1], int(largeur * rayon), outline=(255, 255, 255, 90), width=2)
    return avec_ombre(s, max(6, largeur // 16), largeur // 22, 150) if ombre else s


def pil_vers_np(im):
    return np.asarray(im.convert('RGBA'), dtype=np.float32) / 255.0


def np_vers_pil(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


# ---------------------------------------------------------------- étalonnage
def etalonner(img, look='sombre'):
    lum = (img @ np.float32([0.299, 0.587, 0.114]))[..., None]
    if look in ('nb', 'bw'): return np.repeat(np.clip((lum - 0.5) * 1.25 + 0.5, 0, 1), 3, axis=2)
    if look in ('chaud', 'warm'): return np.clip(img * np.float32([1.08, 1.0, 0.86]) + 0.02, 0, 1)
    if look in ('froid', 'cool'): return np.clip(img * np.float32([0.9, 1.0, 1.1]), 0, 1)
    if look in ('vif', 'pop'): return np.clip(((lum + (img - lum) * 1.35) - 0.5) * 1.12 + 0.5, 0, 1)
    # « sombre » : moins saturé, ombres bleutées, hautes lumières chaudes
    o = np.power(np.clip(lum + (img - lum) * 0.6, 0, 1), 1.3) * 0.88
    o = o + (1 - lum) * np.float32([-0.03, 0.035, 0.065]) + lum * np.float32([0.05, 0.015, -0.04])
    return np.clip((o - 0.42) * 1.12 + 0.42, 0, 1)


def varier(im, i):
    looks = ('vif', 'nb', 'chaud', 'froid', 'sombre')
    return np_vers_pil(etalonner(np.asarray(im.convert('RGB'), np.float32) / 255, looks[i % len(looks)]))


# ---------------------------------------------------------------- la scène
class Scene:
    """L'image en cours : img (H, W, 3), masque de la personne (H, W), visage (x, y, largeur),
    t = temps depuis le début de l'effet, d = durée de l'effet, o = options."""
    __slots__ = ('img', 'masque', 'W', 'H', 'vx', 'vy', 'vt', 't', 'temps', 'fps', 'u')

    def face(self):
        return self.vx, self.vy, self.vt


def composer(s, calque, x, y, alpha=1.0, derriere=False, protege=False):
    """Pose un calque RGBA (PIL ou numpy) avec son coin haut-gauche en (x, y).
    derriere=True : invisible là où se trouve la personne (le calque passe derrière elle).
    protege=True  : ne s'efface que sur le visage, pour ne jamais le cacher."""
    L = pil_vers_np(calque) if isinstance(calque, Image.Image) else calque
    h, w = L.shape[:2]; x, y = int(round(x)), int(round(y))
    a0, b0, a1, b1 = max(0, x), max(0, y), min(s.W, x + w), min(s.H, y + h)
    if a1 <= a0 or b1 <= b0 or alpha <= 0: return
    L = L[b0 - y:b1 - y, a0 - x:a1 - x]
    a = L[..., 3:4] * alpha
    m = s.masque[b0:b1, a0:a1, None]
    if derriere:
        a = a * (1 - m)
    elif protege:
        yy, xx = np.ogrid[b0:b1, a0:a1]
        ell = ((xx - s.vx) / (s.vt * 0.95)) ** 2 + ((yy - s.vy) / (s.vt * 1.35)) ** 2
        a = a * (1 - np.clip((1.2 - ell) / 0.3, 0, 1)[..., None] * m)
    zone = s.img[b0:b1, a0:a1]
    zone[:] = zone * (1 - a) + L[..., :3] * a


def poser(s, im, cx, cy, echelle=1.0, angle=0.0, alpha=1.0, derriere=False, protege=False):
    """Pose une image PIL centrée en (cx, cy), avec échelle et rotation (degrés)."""
    if echelle <= 0.01 or alpha <= 0: return
    if abs(echelle - 1) > 0.004:
        im = im.resize((max(1, int(im.width * echelle)), max(1, int(im.height * echelle))), Image.BILINEAR)
    if abs(angle) > 0.05: im = im.rotate(angle, Image.BICUBIC, expand=True)
    composer(s, im, cx - im.width / 2, cy - im.height / 2, alpha, derriere, protege)


def zoom(s, z, cx, cy):
    """Caméra virtuelle : zoom vers (cx, cy), plafonné à 2x pour garder la netteté."""
    z = min(float(z), 2.0)
    if z <= 1.002: return
    lw, lh = s.W / z, s.H / z
    x0, y0 = borne(cx - lw / 2, 0, s.W - lw), borne(cy - lh / 2, 0, s.H - lh)
    M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
    s.img = cv2.warpAffine(s.img, M, (s.W, s.H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    s.masque = cv2.warpAffine(s.masque, M, (s.W, s.H), flags=cv2.INTER_LINEAR)
    s.vx, s.vy, s.vt = (s.vx - x0) * z, (s.vy - y0) * z, s.vt * z


def zoom_visage(s, z, hauteur_tete=0.40):
    z = min(float(z), 2.0)
    zoom(s, z, s.vx, s.vy + (s.H / z) * (0.5 - hauteur_tete))


def assombrir_bords(s, force=0.35):
    yy, xx = np.ogrid[0:s.H, 0:s.W]
    d = ((xx - s.W / 2) / (s.W * 0.75)) ** 2 + ((yy - s.H / 2) / (s.H * 0.7)) ** 2
    s.img *= (1 - force * np.clip(d, 0, 1).astype(np.float32))[..., None]


def personne_devant(s, avant):
    """Remet la personne (prise dans `avant`) par-dessus tout ce qui a été dessiné depuis."""
    m = s.masque[..., None]
    s.img = s.img * (1 - m) + avant * m


def entree_sortie(s, e, t_in=0.25, t_out=0.2):
    a = borne(s.t / t_in) if t_in else 1.0
    return a * (borne((e.d - s.t) / t_out) if t_out else 1.0)


def apparait(s, t0, duree=0.3):
    return rebond((s.t - t0) / duree) if s.t > t0 else 0.0


def memo(e, cle, fabrique):
    if cle not in e.memo: e.memo[cle] = fabrique()
    return e.memo[cle]
