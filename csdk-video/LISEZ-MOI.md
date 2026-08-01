# Publicité vidéo — Complexe Scolaire Diawoye Kanté

Spot vertical 9:16, 46,33 secondes, en 4K natif (2160 × 3840).
Voix off française incluse et déjà masterisée.

## Il ne manque que les photos

Copie tes 21 visuels dans le dossier `assets/source/`, **en gardant
exactement les noms d'origine**. Les chemins sont déjà écrits dans la
composition : aucune ligne de code à modifier.

Liste attendue :

```
apprendre aujourdhui.jpg     Logo.jpg
artiste.jpg                  médecin.jpg
au complexe csdk.jpg         photo de profil.jpg
avance vers  la reussite.jpg reseaux.jpg
chaque enfants.jpg           reussir demain.jpg
enseignante.jpg              s'epanouir.jpg
entrepreneur.jpg             télécharger.jpg
ici vos enfants.jpg          un bon depart.jpg
Ingénieur.jpg                un environnement.jpg
les grands reves.jpg         un reve.jpg
localisation.jpg
```

Attention : `avance vers  la reussite.jpg` comporte **deux espaces**
entre « vers » et « la ». C'est le nom d'origine, il faut le conserver.

## Rendre la vidéo

Il faut Node.js, ainsi que FFmpeg et Chrome, que l'outil installe seul
au premier lancement.

```bash
# Contrôle avant rendu (mise en page, mouvement, contrastes)
npm run check

# Aperçu interactif dans le navigateur
npm run dev

# Rendu final : 4K, 60 images/seconde, qualité haute
npx hyperframes render -q high -f 60 -o renders/csdk-final.mp4
```

Le rendu est long : comptez environ une heure en 24 fps sur quatre
cœurs, davantage en 60 fps. Sur une machine plus puissante, ce sera
sensiblement plus rapide. Pour un premier essai, `-q draft -f 24` suffit.

## Ce que contient la composition

Dix scènes enchaînées, calées au dixième de seconde sur la voix off :

| # | Scène | Mouvement de caméra |
|---|-------|---------------------|
| 1 | Chaque enfant porte un rêve | Dolly in |
| 2 | Les cinq métiers | Whip-pan alterné |
| 3 | Un bon départ | Tilt up + push |
| 4 | L'école | Crane down |
| 5 | Les trois piliers | Pan latéral |
| 6 | L'environnement | Parallaxe à deux vitesses |
| 7 | Logo et slogan | Révélation, rotation douce |
| 8 | Localisation | Pin rebondissant |
| 9 | Téléphones | Entrées opposées |
| 10 | Clap de fin | Flash + verrouillage |

## Organisation des fichiers

```
index.html          la composition entière
assets/vo/          les 10 segments de voix off
assets/vo-master.mp3 la voix off montée et masterisée
assets/source/      ← tes 21 photos vont ici
vendor/gsap.min.js  la librairie d'animation, en local
build-vo.sh         régénère la voix off et affiche les durées
```

## Deux points techniques à connaître

**GSAP est vendorisé** dans `vendor/`. La composition ne dépend d'aucun
CDN et se rend hors ligne.

**Les calques sont volontairement peu nombreux.** En 4K, chaque surface
plein écran coûte cher à la capture : au-delà d'une trentaine de calques
lourds (`filter: blur`, `mix-blend-mode`, `will-change`), le moteur se
fige ou produit des images noires. Les habillages ont donc été fusionnés
en un seul calque par scène. Si tu ajoutes des effets, garde cette
contrainte en tête.

## Réglages utiles

La charte est définie en haut du fichier `index.html`, dans le bloc
`:root` — bleu marine `#04122B`, or `#F5B921`. Modifier ces valeurs
change toute la vidéo d'un coup.

Les durées de chaque scène sont portées par les attributs `data-start`
et `data-duration`. Si tu retouches la voix off, relance `build-vo.sh`
pour obtenir les nouvelles durées, puis reporte-les.
