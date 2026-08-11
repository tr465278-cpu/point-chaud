# Projet vidéo CSDK — mémoire de production

Ce fichier est lu automatiquement au début de chaque session. Il consigne ce
que la production du premier spot a coûté à découvrir, pour que la suivante
n'ait pas à le repayer.

---

## 1. Contraintes réseau de cet environnement — À LIRE EN PREMIER

La session tourne dans un conteneur Linux distant derrière un proxy strict.
**Ne pas perdre de temps à tester ces accès, ils sont fermés :**

| Bloqué | Conséquence |
| --- | --- |
| `huggingface.co` | Pas de Whisper (transcription), pas de MusicGen (musique IA) |
| Tous les domaines `heygen.com` | Catalogue BGM, images et voix HeyGen inaccessibles |
| Tous les domaines `canva.com` et `design.canva.ai` | On peut **commander** une génération via le MCP Canva, mais **pas récupérer** le fichier |
| `cdn.jsdelivr.net` et les CDN | GSAP doit être vendorisé en local (`vendor/gsap.min.js`) |
| `drive.google.com` | Le connecteur Google Drive **tronque les fichiers binaires** — un JPEG de 18 Ko en est ressorti à 15 Ko, corrompu |

**Ce qui marche :** `registry.npmjs.org`, `github.com`, `raw.githubusercontent.com`,
`www.googleapis.com`, et le proxy git local **en lecture ET en écriture**.

**Transfert de fichiers avec le client : passer par GitHub.** Créer le dossier
cible avec un fichier témoin (Git n'enregistre pas les dossiers vides), pousser,
puis donner le lien — le client dépose par « Add file → Upload files ». Cette
voie a fonctionné du premier coup pour 21 photos et pour la voix off.

---

## 2. Performance de rendu — le piège qui bloque la capture

En 2160×3840, la capture se fige à l'image 0 si la composition est trop lourde.
Diagnostic : une composition minimale au même format rend en 12 s ; si elle
passe et pas la vôtre, c'est la charge de calques.

**Les trois coupables, par ordre de gravité :**

1. **Les surfaces plein écran.** Une V1 en comptait 50 (teinte, deux voiles,
   vignette et grain × 10 scènes). Les fusionner en **un seul calque par scène**,
   voire un seul global, en empilant les dégradés dans une même propriété
   `background`.
2. **`filter: blur()`.** Ruineux à cette définition. Un `radial-gradient` ou un
   `linear-gradient` à arrêts multiples donne le même flou visuel pour rien.
3. **`will-change`.** Force un calque GPU par élément, soit 33 Mo chacun en 4K.
   GSAP gère très bien sans.

`mix-blend-mode` impose aussi une passe de composition par image : à éviter.

Le linter prévient (`composition_heavy_overlay_count_high`) — **le croire**.

**Durées observées** sur 4 cœurs, 48 s en 2160×3840 : 75 à 100 min en 60 fps
qualité haute, ~50 min en 24 fps brouillon. Prévoir large et lancer en tâche de
fond. Le conteneur a redémarré deux fois en pleine production : **committer et
pousser avant chaque rendu**.

**Journaux hors de `/tmp`** — il est effacé au redémarrage.

`nice` empêche le lancement de FFmpeg par le moteur : ne pas l'utiliser.

---

## 3. Le piège d'empilement qui a masqué toutes les photos

Un fond de secours en `::before` avec `z-index: -1` ne passe sous le fond de son
parent **que si celui-ci crée un contexte d'empilement**. `will-change` en
créait un ; en le supprimant pour la performance, le dégradé est repassé
**par-dessus** les photos. Un rendu complet de 93 min a été perdu ainsi.

**Règle :** un repli se met en `background-color` sur l'élément lui-même, peint
par construction sous `background-image`. Jamais en pseudo-élément.

**Toujours vérifier par capture avant un rendu long.** Un petit script Puppeteer
qui charge la composition, appelle `seek(t)` et applique la visibilité des
`.clip` coûte 30 secondes et évite d'en perdre 90.

---

## 4. Calage sur une voix off fournie

Sans transcription (Whisper bloqué), la méthode qui a marché :

1. Détecter les phrases par silences : `silencedetect=noise=-35dB:d=0.28`
2. Traiter la parole comme un **ruban continu**, silences exclus
3. Y projeter le script **au prorata des syllabes** — pas au prorata d'une
   version TTS de référence, dont le débit diffère

**Contrôle de justesse :** le débit en syllabes/seconde doit être à peu près
constant d'une réplique à l'autre. S'il varie de 2,6 à 6,5, le calage dérive.
Compter les nombres en toutes lettres (« 74 » = quatre syllabes), sinon la
réplique des téléphones est massivement sous-estimée.

**Anticipation obligatoire.** Une animation d'entrée doit **se poser** sur le
mot, pas démarrer dessus : commencer 0,30 s avant. Sans ça le texte paraît en
retard d'une demi-seconde, et le client le voit.

Le client a finalement peaufiné le calage final dans CapCut — c'est le bon
outil pour ça, avec la forme d'onde sous les yeux.

---

## 5. Doctrine de mouvement — les paramètres retenus

Charger `motion-doctrine` avant toute composition, puis `cut-the-curve` pour les
paramètres. Ce qui a servi ici :

- **Un courant unique** — toutes les coupes ordinaires vont dans la même
  direction (gauche par défaut). Les autres vecteurs sont réservés au sens :
  poussée en Z pour entrer dans un sujet, zoom inverse pour une arrivée.
- **Déplacement partiel : ~12 % du cadre**, jamais une sortie complète.
- **Eases miroir** : sortie `power4.in`, entrée `power4.out`, même distance et
  même durée — les deux moitiés d'un `power4.inOut`.
- **Signe en Z** : d(échelle)/dt doit garder le même signe des deux côtés d'une
  coupe. Une sortie qui rétrécit suivie d'une entrée qui grandit est le défaut
  le plus courant.
- **`bounce.out` et `elastic.out` sont proscrits.** Un dépassement d'entrée en
  `back.out(1.4–1.7)` est admis.
- **Pas d'oscillation d'attente.** Une forme qui flotte sur place fait lire « la
  vidéo attend ». Les décors avancent en trajectoire monotone.
- Entrée ≤ 800 ms · sortie ≈ 75 % de l'entrée · 2 à 3 transitions par film,
  répétées. La variété se met **dans** les scènes, pas dans les coupes.
- `#root` doit avoir un fond opaque, sinon les coupes à opacité cumulée < 1
  laissent passer un flash blanc.

---

## 6. Grammaire texte / image validée par le client

Trois traitements, décidés scène par scène :

- **Synchronisé** — photo et texte animé ensemble
- **Photo seule** — l'image se suffit, aucun texte
- **Texte animé seul** — le texte porte le message ; corps nettement plus grand
  (250 px contre 190 px), mot-clé isolé sur sa ligne, décor accéléré

Le principe : quelqu'un qui regarde sans le son doit pouvoir suivre.

---

## 7. Ressources du projet

**Organisation du dépôt.** Un dossier de montage par spot — `csdk-video/`
(publicité 1), `pub2-video/` (publicité 2) — et un dossier de dépôt client par
spot à venir — `publicite-2/`, `publicite-3/` — avec `audio/`, `photos/` et un
`LISEZ-MOI.md` qui sert de gabarit de brief. Les masters partent dans
`livraison/` du dossier de dépôt correspondant.

**Charte** : bleu marine `#04122B` / `#08203F` · or `#F5B921` · blanc.
La publicité 2 en décline une variante éditoriale : `--ink #061530`,
`--ink-2 #0A2148`, `--gold #F5B921`, `--grey #8FA3C4`.

**Voix off** : `assets/voix-finale.mp3`, ElevenLabs (voix Victoria,
`eleven_multilingual_v2`), 48,33 s, fournie par le client.
Kokoro (le TTS local) n'a **aucune voix masculine française** — seule `ff_siwis`
est native, et elle est féminine. Les voix masculines anglophones passées au
phonémiseur français ont été rejetées à l'écoute.

**21 photos** dans `assets/source/`, entre 736 et 1080 px de large. C'est la
limite de netteté du rendu, pas le montage — en vignettes elles passent bien
mieux qu'en plein écran.

**19 bruitages** livrés en local avec le skill `media-use`, dans
`.claude/skills/media-use/audio/assets/sfx/` : whoosh ×3, impact-bass ×2, pop,
click ×2, riser, sparkle, chime, ping, glitch ×2, typing. Ils ont été écartés du
montage final — le client les trouvait trop couvrants sur la voix.

**Décision du client à ne pas rediscuter** : la photo d'Elon Musk reste sur la
scène « entrepreneur », et `un bon depart.jpg` reste sur « Grandissent avec
confiance ». Le risque lié au droit à l'image a été signalé, le client l'assume.

---

## 8. Les 25 skills — quel skill pour quoi

`npx skills add heygen-com/hyperframes` installe l'ensemble.
`npx hyperframes skills update` ne récupère **que le noyau de 8**.

| Besoin | Skill |
| --- | --- |
| Point d'entrée, routage | `hyperframes` |
| Loi du mouvement, continuité entre scènes | `motion-doctrine` **(à charger en premier)** |
| Paramètres de transitions et d'entrées | `cut-the-curve` |
| Mécanique de rendu des coupes, flash blanc | `seam-craft` |
| Structure, attributs `data-*`, déterminisme | `hyperframes-core` |
| Animation, blueprints, 24 effets de texte | `hyperframes-animation` |
| Keyframes, GSAP, masques, SVG, 3D | `hyperframes-keyframes` |
| Palette, typographie, narration, beats | `hyperframes-creative` |
| Musique, bruitages, images, voix, étalonnage | `media-use` |
| CLI : init, check, render, publish | `hyperframes-cli` |
| Blocs et composants prêts à l'emploi | `hyperframes-registry` |
| Pub produit à partir d'une URL ou d'un brief | `product-launch-video` |
| Explicatif sans visage | `faceless-explainer` |
| Vidéo calée sur une musique | `music-to-video` |
| Motion graphic court, sans narration | `motion-graphics` |
| Sous-titres sur du rush existant | `embedded-captions` |
| Habillage graphique sur du rush | `talking-head-recut` |
| Tout le reste, multi-scènes | `general-video` |

---

## 9. Publicité 2 — ce que la deuxième production a appris

Dossier `pub2-video/`, direction **éditoriale magazine** (choisie par le client
pour ne pas ressembler au premier spot) : cadres à angles vifs, folios chiffrés
`01`–`04`, surtitres très espacés, filets or qui se tracent, grille de colonnes
visible en fond. Même charte bleu marine / or, vocabulaire visuel entièrement
différent. 47,1 s · 15 scènes · 16 répliques.

**Les emojis à l'écran.** Le client en voulait de vrais (🙅 🫵👍). Un emoji
system échoue au lint (`font_family_without_font_face`) et ne rend pas en
couleur à la capture. La solution : copier `NotoColorEmoji.ttf` dans
`assets/fonts/` et le déclarer.

```css
@font-face { font-family:"CSDK Emoji";
  src:url("assets/fonts/NotoColorEmoji.ttf") format("truetype");
  font-display:block; }
```

Le fichier pèse 10,8 Mo — il doit être versionné, pas ignoré.

**Coupures de mots en plein milieu.** « COMPLEXE SCOLAIR·E », « INSCRIPTIO·NS ».
Le moteur coupe sans césure quand le mot dépasse. Ça ne se corrige pas par
`overflow`, seulement en **réduisant le corps** : 186 → 152 px pour les titres
longs, 236 → 172 px pour l'affiche. Vérifier chaque scène par capture.

**`align.py` affiné.** Version de référence dans `pub2-video/align.py` :
`silencedetect` à `d=0.25` (au lieu de 0,28), table `NUM` pour les nombres en
toutes lettres, projection sur le ruban de parole par `wall(pos)`. Résultat sur
la voix de la publicité 2 : **5,80 syll/s constant sur les 16 répliques, aucun
chevauchement** — c'est le signe que le calage est juste.

**Vocabulaire d'animation retenu** (tous avec `LEAD = 0.30`) : `wipe` (volet),
`letter` (lettre à lettre), `type` (frappe), `press` (impression typographique)
et `draw()` pour les filets or. Quatre gestes suffisent : la variété vient du
rythme, pas du nombre d'effets.

**Rendu** : 97 min en 2160×3840 · 60 fps, après un redémarrage de conteneur qui
a tué la première tentative. Contrôles au vert : 0 erreur de lint, de mise en
page et de mouvement, **166 contrastes sur 166 conformes AA**, 0 image noire sur
16 points de sondage.

**Réserve signalée au client** : les quatre visuels des piliers sont des
illustrations bleues, pas des photographies. Remplaçables s'il fournit mieux.

---

## 10. Boucle de travail

```bash
npm run check      # lint + mise en page + mouvement + contraste
npm run render     # rendu MP4
```

`npm run check` doit être au vert avant tout rendu. Il a attrapé deux vrais
défauts invisibles à l'œil : des pastilles à 1,1:1 de contraste (illisibles) et
une vignette qui recouvrait le texte.

**Livraison** : master 4K + version 1080×1920 réduite en Lanczos. La 1080 est
souvent **plus belle** que la 4K quand les photos sources sont petites, et c'est
le format natif des réseaux. La messagerie plafonne à 30 Mo : au-delà, déposer
dans `livraison/` sur GitHub.
