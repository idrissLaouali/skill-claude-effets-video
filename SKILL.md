---
name: effets
description: Ajoute un des 45 effets vidéo (plus des sous-titres mot par mot) à une vidéo face caméra, en français. Orbite, projecteur, widgets en verre, timeline, liste de tâches Claude, mur de titres, commentaire Instagram, éventail de téléphones, graphique en verre liquide, raccord, interrupteurs iPhone, enseigne LED, zoom par-dessus l'épaule, messages, grille de profil et plus. Les effets suivent le visage et peuvent passer derrière la tête. À utiliser quand on tape /effets, qu'on nomme un effet, ou qu'on demande d'ajouter un effet, un zoom, un étalonnage, un sticker, des sous-titres ou une animation à une vidéo.
---

# Effets : 45 effets vidéo en français (par Idriss Laouali, Karatou Academy)

La personne n'est souvent pas technique. Réponds court, en français, fais le travail à sa place et ne lui demande jamais de lancer des commandes.

Tous les chemins ci-dessous partent du dossier de ce skill (celui qui contient ce SKILL.md). Utilise son chemin absolu dans les commandes.

## 1. Première fois : installation (une seule fois)
Lance `bash scripts/installer.sh`. Il affiche `PRET` quand c'est bon (1 à 3 minutes la première fois).
- `BESOIN_FFMPEG` : installe-le pour elle. Mac : `brew install ffmpeg` (sans `brew`, dis-lui d'installer Homebrew depuis brew.sh). Windows : `winget install ffmpeg`.
- `BESOIN_PYTHON` : installe Python 3.12 (Mac : `brew install python@3.12`, Windows : `winget install Python.Python.3.12`), puis relance l'installation.
- Sur Windows, Python est dans `.venv\Scripts\python.exe` au lieu de `.venv/bin/python`.

## 2. La vidéo et l'effet
- Vidéo : glissée dans la discussion ou donnée par son chemin. Une vidéo verticale de téléphone marche le mieux.
- Effet : depuis `/effets <nom>`, ou d'après ce que la personne décrit. Fais correspondre ses mots au tableau plus bas. Les noms anglais marchent aussi. En cas de doute, montre la liste (`.venv/bin/python scripts/effets.py --liste`).

## 3. Le bon moment
- Si elle dit « sur le mot X » ou « quand je dis ... », lance `.venv/bin/python scripts/transcrire.py <video>` (la première fois : `.venv/bin/pip install faster-whisper`). Il écrit `<video>_mots.json` et affiche chaque mot avec son temps.
- Sans indication, mets l'effet sur tout le clip ou pose une seule question courte.
- Les fenêtres courtes rendent mieux : 1,5 à 4 secondes par effet.

## 4. Brouillon, vérification, rendu
1. Écris le plan à côté de la vidéo, `<nom-video>_effets.json` :
   ```json
   {"effets": [
     {"effet": "orbite", "debut": 3.2, "fin": 6.0},
     {"effet": "mot-geant", "debut": 14.0, "fin": 16.3, "texte": "KARATOU"}
   ]}
   ```
   Les clés anglaises (`effects`, `fx`, `start`, `end`, `text`) sont acceptées aussi.
2. Vérifie d'abord des images (rapide) : `.venv/bin/python scripts/effets.py --plan <plan.json> <video> <dossier>/verif.png --apercu 4.5,15.2`, au milieu de chaque effet. Regarde les PNG toi-même. Corrige le texte, le moment ou les options si quelque chose cloche (texte sur le visage, coupé par le bord, illisible).
3. Rendu : `.venv/bin/python scripts/effets.py --plan <plan.json> <video> <nom-video>_effets.mp4`. Le son d'origine est gardé. Sortie en 1080p ; ajoute `--largeur 2160` pour la 4K (plus lent).
4. Dis-lui où est le fichier et rappelle-lui en une ligne de regarder avant de publier : tu prépares, elle valide.

Un seul effet, sans plan : `.venv/bin/python scripts/effets.py orbite <video> <sortie.mp4> --debut 3 --fin 6 --texte "..." --opt cle=valeur`.

## Les effets
Les listes s'écrivent avec `|` (ex. `texte=Un|Deux|Trois`). Les couleurs en hexadécimal (`couleur=#F5A623`). `images` = un dossier de captures ou de clips (sinon des images de ta vidéo sont utilisées).

| # | Nom | Ce que ça fait | Options (toutes facultatives) | Nom anglais |
|---|---|---|---|---|
| 1 | `verrouille` | Des crochets se verrouillent sur ton visage et la caméra te suit | `texte`, `zoom` | `locked-on` |
| 2 | `plongee` | Un zoom rapide sur un mot, pour appuyer une phrase | `vitesse`, `zoom` | `lean-in` |
| 3 | `poussee-lente` | Une poussée cinéma lente vers ton visage, la pièce devient floue | `flou`, `zoom` | `slow-push` |
| 4 | `projecteur` | Les lumières s'éteignent, toi tu restes éclairé (look=paillettes pour la version dorée) | `couleur`, `look`, `police`, `pousse`, `texte` | `spotlight` |
| 5 | `ambiance` | Un étalonnage cinéma : plus sombre, plus doux (look=sombre, nb, chaud, froid, vif) | `look` | `moody` |
| 6 | `avant-apres` | Un curseur avant / après balaie l'image | `apres`, `avant`, `look` | `swipe` |
| 7 | `tunnel` | L'image s'enfonce dans elle-même en tournant, toi tu restes devant | `ratio`, `rotation`, `vitesse` | `rabbit-hole` |
| 8 | `points` | L'image se construit en points lumineux, puis devient nette | `cellule`, `couleur`, `fond` | `dot-reveal` |
| 9 | `pause-fleche` | Arrêt sur image, une flèche dessinée à la main pointe vers toi | `couleur`, `texte`, `x_texte` | `pause-point` |
| 10 | `desinstallation` | Une barre de désinstallation glitchée qui casse l'image | `texte` | `uninstall` |
| 11 | `cadre-reel` | Ta vidéo rétrécit dans une carte de reel Instagram | `texte` | `reel-frame` |
| 12 | `widgets-verre` | Des widgets en verre et des mini-pages flottent autour de ta tête, avec « Monté par Claude » | `compte`, `date`, `evenement`, `jour`, `look`, `nom`, `pastille`, `piste`, `sombre`, `sous`, `texte`, `titre`, `vues` | `glass-widgets` |
| 13 | `graphique-verre` | Une carte en verre liquide sous ton menton : la courbe monte et le chiffre défile (look=bento pour la version tableau de bord) | `a`, `anneau`, `barres`, `couleur`, `de`, `kpi`, `look`, `texte` | `liquid-glass-graph` |
| 14 | `zoom-epaule` | La caméra plonge dans un coin, un graphique en verre apparaît près de ta tête, puis l'autre coin avec un second graphique | `a`, `texte`, `zoom` | `over-the-shoulder-zoom` |
| 15 | `messages` | Des notifications de messages apparaissent une à une, en verre crème avec un halo doux | `texte`, `titre`, `y` | `imessage` |
| 16 | `taches-claude` | Une liste de tâches Claude sous ton menton : chaque étape tourne, puis se coche en vert | `texte`, `titre` | `checklist` |
| 17 | `interrupteurs` | Une carte de réglages iPhone au-dessus de toi : les interrupteurs s'allument un par un | `chevauche`, `couleur`, `moments`, `pos`, `texte`, `ticks`, `zoom` | `apple-toggles` |
| 18 | `mot-geant` | Un mot géant tombe derrière toi | `couleur`, `police`, `texte` | `backdrop-word` |
| 19 | `ticket` | Tes consignes s'impriment comme un ticket de caisse, dans le mur au-dessus de ta tête | `texte` | `the-bill` |
| 20 | `tampon` | Un gros tampon rouge s'écrase sur l'image | `angle`, `couleur`, `texte`, `y` | `reject-stamp` |
| 21 | `compte-a-rebours` | Une horloge à volets 3, 2, 1 au-dessus de ta tête | `depuis` | `countdown-flip` |
| 22 | `couverture` | Tu deviens la couverture d'un magazine, le titre derrière ta tête (look=editorial pour la version classique) | `accent`, `couleur`, `droite`, `droite_y`, `lignes`, `lignes_y`, `look`, `numero`, `texte` | `cover-star` |
| 23 | `griffonnage` | Des dessins au feutre se tracent tout seuls autour de toi | `couleur`, `texte` | `scribble` |
| 24 | `collage-rouge` | Toi en noir et blanc, un mot rouge géant derrière, trois lignes qui claquent | `couleur`, `etiquette`, `lignes`, `texte` | `red-collage` |
| 25 | `titre-partage` | Un bandeau titre descend et te pousse dans la moitié basse de l'image | `couleur`, `fort`, `hauteur`, `pastille`, `pousse`, `texte` | `split-headline` |
| 26 | `mot-pastel` | Fond lavande, un mot géant derrière toi et une carte de profil qu'on suit | `compte`, `nom`, `role`, `texte` | `pastel-word` |
| 27 | `titre-encadre` | Un zoom avec un titre sur deux lignes, la seconde dans un cadre blanc | `texte`, `zoom` | `headline-box` |
| 28 | `mur-titres` | Tes propres titres de reels s'empilent derrière ta tête, puis ton total de vues apparaît devant | `compte`, `ecart`, `libelle`, `nombre`, `texte`, `total` | `headline-wall` |
| 29 | `raccord` | Des pages de journaux défilent en coupant sur un seul mot, figé derrière ta tête | `couleur`, `texte` | `match-cut` |
| 30 | `enseigne` | La lumière baisse et une enseigne LED s'écrit derrière toi | `couleur`, `pousse`, `texte` | `led-sign` |
| 31 | `classement` | Un classement S à F tombe devant toi et Claude file tout en haut | `autres`, `element`, `titre` | `tier-list` |
| 32 | `a-faire` | Une liste à faire à côté de ta tête, cochée au fil de tes mots | `moments`, `texte`, `ticks`, `titre` | `todo` |
| 33 | `alignement` | Des tuiles numérotées s'ouvrent en éventail au-dessus de ta tête | `texte` | `lineup` |
| 34 | `avalanche` | Tes reels s'empilent derrière ta tête, un tous les quarts de seconde | `images`, `taille` | `noise` |
| 35 | `orbite` | Tes reels tournent autour de ta tête : devant en bas, derrière en haut | `images`, `nombre`, `taille`, `vitesse` | `orbit` |
| 36 | `carrousel` | Tes reels tournent autour de toi en carrousel 3D, puis ralentissent | `images`, `nombre`, `taille`, `tours` | `carousel-spin` |
| 37 | `eventail-telephones` | Tes reels s'ouvrent comme un jeu de cartes de téléphones, sous un titre | `images`, `texte` | `phone-fan` |
| 38 | `broll-partage` | Écran partagé : un B-roll en haut avec une étiquette, toi en bas | `choix`, `images`, `texte` | `broll-split` |
| 39 | `pastilles` | Pièce en papier quadrillé, tes reels épinglés derrière toi, un curseur clique des pastilles bleues | `compte`, `images`, `tableau`, `texte` | `check-pills` |
| 40 | `pluie-touches` | Des touches de clavier tombent en pluie derrière toi | `nombre`, `texte` | `shortcut-rain` |
| 41 | `mur-profil` | Ta grille de profil remplit le mur derrière toi pendant qu'un compteur défile | `images`, `libelle`, `nom`, `nombre`, `sous` | `profile-wall` |
| 42 | `grille-profil` | Tu rétrécis au centre de ta grille 3x3, tes reels apparaissent autour avec leurs vues | `images`, `vues` | `place-in-grid` |
| 43 | `commentaire` | Une fenêtre de commentaires Instagram au-dessus de ta tête : ton mot s'écrit, se publie, reçoit un cœur et ta réponse (look=barre pour la version simple) | `compte`, `look`, `puce`, `reponse`, `texte` | `comment-box` |
| 44 | `abonnement` | Un bouton « S'abonner » apparaît et passe à « Abonné » | `a`, `couleur`, `x`, `y` | `tap` |
| 45 | `timeline` | Un look cinéma rouge sombre avec une timeline de montage, un compteur REC et une tête de lecture lumineuse | `couleur`, `sous`, `texte` | `auto-edit` |
| 46 | `sous-titres` | Bonus : sous-titres mot par mot en français, le mot prononcé s'allume en or (mots=fichier de transcrire.py) | `casse`, `couleur`, `mots`, `paquet`, `taille`, `y` | `captions` |

**Looks** (même effet, autre style, ne comptent pas dans les 45) :
- `projecteur` avec `look=paillettes` : la pièce s'éteint, des rayons dorés derrière ta tête, un grand mot doré qui brille.
- `couverture` avec `look=editorial` : film chaud et doux, titre classique en serif, lignes de couverture élégantes.
- `graphique-verre` avec `look=bento` : la courbe passe sur un écran fumé derrière toi, avec des tuiles en verre devant (anneau, chiffre clé, barres).
- `commentaire` avec `look=barre` : la simple barre de commentaire qui tape le mot et le publie.

**Bonus Karatou** : `sous-titres` avec `mots=<video>_mots.json` (de `transcrire.py`). Mot par mot, en majuscules, le mot prononcé s'allume en or. Options : `couleur`, `y` (0 à 1, défaut 0,74), `paquet` (mots par ligne, défaut 3), `taille`, `casse=normale`.

## Règles
- Ne couvre jamais le visage. Tout passe derrière la personne ou évite le visage tout seul ; si une image de vérification montre du texte sur le visage, déplace-le (`x`, `y`) ou raccourcis le texte.
- Les effets s'appliquent dans l'ordre du plan. Mets les effets caméra (`verrouille`, `plongee`, `projecteur`) en premier quand ils se chevauchent avec d'autres.
- Le zoom ne dépasse jamais 2x, pour garder une image nette.
- Ce sont des versions de départ. Sois honnête si la personne les compare à un reel qu'elle a vu.
