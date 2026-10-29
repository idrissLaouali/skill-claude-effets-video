"""Bande son Karatou : musique et bruitages synthétisés ici (libres de droits), calés sur le plan d'effets.

Recette (celle de nos reels) :
- hook sonore : silence tendu (cœur, tic-tac, drone qui monte, riser) puis DROP (impact + basse 808) ;
- avant chaque effet : le beat s'arrête, riser + cymbale inversée = suspense ;
- sur chaque effet : DROP, puis un beat trap à 150 BPM jusqu'à l'effet suivant ;
- un son propre à chaque effet (clics, souffle, choc, pops de verre...) ;
- la voix d'origine reste devant : la musique baisse dès que tu parles.
"""
import subprocess, wave
import numpy as np

SR = 44100
_rng = np.random.default_rng(7)


def _tt(d): return np.arange(int(d * SR)) / SR


def _lp(x, a):
    y = np.empty_like(x); v = 0.
    for k in range(len(x)): v += a * (x[k] - v); y[k] = v
    return y


def _hp(x, a): return x - _lp(x, a)


def b808(note=55, d=1.1):
    t = _tt(d); f = note * (1 + 1.2 * np.exp(-t * 30)); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    x = np.tanh(x * 2.5) * .9; x[:200] *= np.linspace(0, 1, 200); return x


def kick():
    t = _tt(.28); f = 48 + 140 * np.exp(-t * 35); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)
    x[:300] += _rng.standard_normal(300) * np.exp(-np.arange(300) / 40) * .4; return np.tanh(x * 1.8)


def clap():
    t = _tt(.25); n = _hp(_lp(_rng.standard_normal(len(t)), .35), .08); x = n * np.exp(-t * 18); y = x.copy()
    for dl, g in ((.021, .4), (.043, .25), (.071, .15)): y[int(dl * SR):] += x[:-int(dl * SR)] * g
    return y * .8


def hat(d=.035, g=1.):
    return _hp(_rng.standard_normal(int(d * SR)), .6) * np.exp(-_tt(d) * 90) * .35 * g


def bell(f, d=.9):
    t = _tt(d)
    x = np.sin(2 * np.pi * f * t) + .45 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6) + .2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 12)
    return x * np.exp(-t * 4.5) * .22


def riser(d, f0=300, f1=2500):
    t = _tt(d); p = t / d; f = f0 * (f1 / f0) ** p
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * .25 + _hp(_rng.standard_normal(len(t)), .2) * .25 * p) * p ** 2


def rev_cymbal(d=.7):
    t = _tt(d); return _hp(_rng.standard_normal(len(t)), .5) * (t / d) ** 3 * .6


def impact():
    t = _tt(1.6); f = 32 + 60 * np.exp(-t * 8); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5)
    n = _lp(_rng.standard_normal(len(t)), .08) * np.exp(-t * 6) * 1.5; return np.tanh((x + n) * 1.6) * .9


def tick():
    t = _tt(.03); return np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 200) * .3


def coeur():
    t = _tt(.18); return np.sin(2 * np.pi * (60 + 30 * np.exp(-t * 20)) * t) * np.exp(-t * 22) * .7


def whoosh(d=.45, monte=True):
    n = _rng.standard_normal(int(d * SR)); y = np.zeros_like(n); v = 0
    for k in range(len(n)):
        p = k / len(n); a = .01 + .3 * (p if monte else 1 - p); v += a * (n[k] - v); y[k] = v
    return y * np.sin(np.linspace(0, np.pi, len(n))) ** 2 * 1.6


def ding(f=1568):
    a = bell(f, 1.2) * 2.2; a[:SR] += bell(f * 1.5, 1.0) * 1.2; return a


MEL = [880, 1046.5, 987.8, 659.3]
BASSES = [(55, 65.4, 49, 55), (49, 55, 65.4, 41.2)]


class Piste:
    def __init__(s, duree):
        s.N = int(duree * SR); s.mus = np.zeros(s.N); s.fx = np.zeros(s.N)
        s.K, s.C = kick(), clap(); s.B8 = {n: b808(n) for n in (55, 49, 65.4, 41.2)}

    def add(s, buf, t, x, g=1.0):
        i = int(t * SR)
        if i >= s.N: return
        if i < 0: x = x[-i:]; i = 0
        n = min(len(x), s.N - i); buf[i:i + n] += x[:n] * g

    def beat(s, t0, t1, intense=1.0, basse=BASSES[0], bpm=150):
        bt = 60 / bpm; t = t0; nb = 0
        while t < t1 - .05:
            for k in range(8):
                x = t + k * bt / 2
                if x >= t1 - .02: break
                s.add(s.mus, x, hat(g=.8 + .4 * (k % 2 == 0)), intense)
                if k == 0: s.add(s.mus, x, s.K, .9 * intense); s.add(s.mus, x, s.B8[basse[nb % 4]], .75 * intense)
                if k == 5: s.add(s.mus, x, s.K, .6 * intense)
                if k == 4: s.add(s.mus, x, s.C, .55 * intense)
                if k in (0, 6): s.add(s.mus, x, bell(MEL[(nb * 2 + (k > 0)) % 4]), .9 * intense)
            if nb % 2 == 1 and t + 4 * bt < t1:
                for r in range(6): s.add(s.mus, t + 3.5 * bt + r * bt / 12, hat(.02, .7), .8 * intense)
            t += 4 * bt; nb += 1

    def hook(s, drop):
        for k in range(int(drop / .4) + 1): s.add(s.fx, .05 + k * .4, tick(), .8)
        for t, g in ((.25, .5), (.5, .35), (1.05, .5), (1.3, .35)):
            if t < drop: s.add(s.fx, t, coeur(), g)
        s.add(s.fx, 0, np.sin(2 * np.pi * 55 * _tt(drop)) * np.linspace(0, .18, int(drop * SR)), 1)
        s.add(s.fx, drop - min(1.4, drop), riser(min(1.4, drop)), .9)
        s.add(s.fx, drop - min(.7, drop), rev_cymbal(min(.7, drop)), .8)

    def drop(s, t, montee=.7):
        if t > .3:
            m = min(montee, t - .05); s.add(s.fx, t - m, riser(m, 400, 3000), .8); s.add(s.fx, t - m * .7, rev_cymbal(m * .7), .7)
        s.add(s.fx, t, impact(), .9)

    def signature(s, nom, t, d):
        f = s.fx
        if nom in ('verrouille', 'pause-fleche', 'abonnement'):
            for k in range(4): s.add(f, t + .15 + k * .09, tick() * 1.5, .9)
            s.add(f, t + .55, ding(2093)[:int(.4 * SR)], .5)
        elif nom in ('orbite', 'carrousel', 'tunnel', 'toupie'):
            s.add(f, t + .1, whoosh(min(1.2, d)), .5)
        elif nom in ('mot-geant', 'tampon', 'collage-rouge', 'enseigne', 'couverture'):
            s.add(f, t + .08, impact(), .7)
        elif nom in ('widgets-verre', 'graphique-verre', 'zoom-epaule', 'messages', 'interrupteurs', 'taches-claude'):
            for k in range(5): s.add(f, t + .1 + k * .14, ding(1568 + 200 * k)[:int(.25 * SR)], .35)
        elif nom in ('projecteur', 'ambiance', 'points'):
            s.add(f, t - .02, clap() * 1.5, .8); s.add(f, t + .2, riser(1.5, 2000, 6000)[::-1], .25)
        elif nom in ('grille-profil', 'mur-profil', 'avalanche', 'pastilles', 'alignement', 'mur-titres', 'pixelisation'):
            for k in range(8): s.add(f, t + .3 + k / 30, tick() * 1.6, .7)
        elif nom in ('commentaire', 'a-faire', 'ticket', 'pluie-touches'):
            for k in range(6): s.add(f, t + .3 + k * .06, tick(), .5)
            s.add(f, t + 1.0, ding(1318.5), .6)
        else:
            s.add(f, t, whoosh(.4), .4)


def lire_audio(video, duree):
    """Le son d'origine de la vidéo (ta voix), en mono 44,1 kHz. Silence s'il n'y en a pas."""
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True)
    v = np.frombuffer(r.stdout, np.int16).astype(np.float64) / 32768 if r.stdout else np.zeros(1)
    out = np.zeros(int(duree * SR)); out[:min(len(out), len(v))] = v[:len(out)]; return out


def bande_son(plan, duree, voix, hook=None, niveau=.42):
    """plan : liste de dicts {nom, debut, fin}. hook : seconde du drop d'ouverture (None = pas de hook)."""
    P = Piste(duree); ev = sorted(plan, key=lambda d: d['debut'])
    if hook:
        P.hook(hook); P.add(P.fx, hook, impact(), 1.0)
        fin_hook = next((d['debut'] - .6 for d in ev if d['debut'] > hook + 1.0), duree)
        P.beat(hook, fin_hook, 1.0)
    for i, d in enumerate(ev):
        t0 = d['debut']; t1 = ev[i + 1]['debut'] if i + 1 < len(ev) else min(duree, d['fin'] + 2.0)
        if hook and abs(t0 - hook) < .3: P.signature(d['nom'], t0, d['fin'] - t0); continue
        P.drop(t0); P.signature(d['nom'], t0, d['fin'] - t0)
        P.beat(t0, max(t0 + .5, t1 - .6) if i + 1 < len(ev) else t1, 1.0 if i % 2 == 0 else .9, BASSES[i % 2])
    e = np.abs(voix); k = int(.08 * SR); e = np.convolve(e, np.ones(k) / k, 'same'); e = e / (e.max() + 1e-9)
    duck = 1 - .55 * np.clip(e * 4, 0, 1)
    m = P.mus / (np.abs(P.mus).max() + 1e-9); f = P.fx / (np.abs(P.fx).max() + 1e-9)
    v = voix / (np.abs(voix).max() + 1e-9) * .95 if np.abs(voix).max() > 1e-4 else voix
    out = v + m * niveau * duck + f * .5 * (1 - .3 * np.clip(e * 4, 0, 1))
    out = np.tanh(out * 1.1) / np.tanh(1.1); return out / (np.abs(out).max() + 1e-9) * .97


def ecrire_wav(chemin, x):
    w = wave.open(chemin, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
