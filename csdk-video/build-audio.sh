#!/usr/bin/env bash
# V3 — Voix off française, traitée en chaîne de voix radio.
#
# ff_siwis est la seule voix nativement française de Kokoro. Les voix
# masculines disponibles sont des timbres anglophones plaqués sur un
# phonémiseur français : écartées après écoute.
#
# La sortie brute du moteur sonne plate. La chaîne ci-dessous lui donne
# la densité et la présence d'une voix publicitaire.
set -u
OUT="assets/vo3"
VOICE="ff_siwis"
SPEED="1.09"          # débit publicitaire, sans déformer le timbre
rm -rf "$OUT"; mkdir -p "$OUT" /tmp/vo-brut

# coupe-bas          supprime le ronflement
# creux 250 Hz       dégage l'effet carton
# présence 2,8 kHz   intelligibilité : la voix sort du mix
# air 7,5 kHz        brillance
# exciter            grain et matière
# compression        densité constante, aucun mot ne retombe
CHAIN="highpass=f=80,\
equalizer=f=250:t=q:w=1:g=-2.5,\
equalizer=f=2800:t=q:w=1.1:g=4,\
equalizer=f=7500:t=h:g=3.5,\
aexciter=amount=2:blend=2,\
acompressor=threshold=-20dB:ratio=4:attack=5:release=90:makeup=4,\
alimiter=level_in=1:level_out=0.95:limit=0.95,\
loudnorm=I=-14:TP=-1.0"

declare -a SEG=(
  "01|Chaque enfant porte un rêve."
  "02|Devenir médecin."
  "03|Enseignante."
  "04|Ingénieur."
  "05|Artiste."
  "06|Entrepreneur."
  "07|Mais tous les grands rêves ont besoin d'un bon départ."
  "08|Au Complexe Scolaire Diawoye Kanté,"
  "09|nous croyons qu'une éducation de qualité peut changer une vie."
  "10|Ici, vos enfants apprennent avec discipline."
  "11|Grandissent avec confiance."
  "12|Et avancent vers la réussite."
  "13|Offrez à votre enfant un environnement pour apprendre,"
  "14|s'épanouir, et construire son avenir."
  "15|Complexe Scolaire Diawoye Kanté."
  "16|Apprendre aujourd'hui, réussir demain."
  "17|Korofina-Nord, près de la pharmacie Fady."
  "18|Appelez-nous au 74 45 45 71, ou au 93 59 92 01."
  "19|Les inscriptions sont ouvertes !"
)

TOTAL=0
echo "--- $VOICE / fr-fr / débit $SPEED / chaîne studio ---"
for entry in "${SEG[@]}"; do
  id="${entry%%|*}"; txt="${entry#*|}"
  raw="/tmp/vo-brut/seg${id}.wav"
  f="$OUT/seg${id}.wav"
  npx --yes hyperframes@0.7.87 tts "$txt" --voice "$VOICE" --lang fr-fr --speed "$SPEED" -o "$raw" >/dev/null 2>&1
  if [ -f "$raw" ]; then
    ffmpeg -y -i "$raw" -af "$CHAIN" -ar 48000 "$f" -loglevel error
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
    TOTAL=$(python3 -c "print(round($TOTAL + $d, 3))")
    printf "seg%s  %6.2fs  %s\n" "$id" "$d" "$txt"
  else
    printf "seg%s  ÉCHEC\n" "$id"
  fi
done
rm -rf /tmp/vo-brut
echo "------------------------------------------------"
echo "TOTAL parole = ${TOTAL}s"
