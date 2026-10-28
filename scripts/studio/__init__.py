"""Registre des effets. Chaque effet a un nom français, des alias (dont les noms anglais courants) et une description."""
EFFETS = {}
ALIAS = {}
AVEC_CARTES = set()   # effets qui utilisent des vignettes de reels


def effet(nom, description, alias=(), cartes=False):
    def deco(fn):
        EFFETS[nom] = (fn, description)
        for a in alias: ALIAS[a] = nom
        if cartes: AVEC_CARTES.add(nom)
        return fn
    return deco


def resoudre(nom):
    n = nom.lower().strip().lstrip('/').replace('_', '-').replace(' ', '-')
    return ALIAS.get(n, n)


class Effet:
    def __init__(self, d):
        self.nom = resoudre(d['effet'])
        self.debut, self.fin = float(d.get('debut', 0)), float(d.get('fin', 1e9))
        self.d = max(0.05, self.fin - self.debut)
        self.o = {k: v for k, v in d.items() if k not in ('effet', 'debut', 'fin')}
        self.memo, self.cartes = {}, []


def charger_tout():
    from . import camera, mots, cartes, interface, verre  # noqa: F401  (enregistrent leurs effets)
