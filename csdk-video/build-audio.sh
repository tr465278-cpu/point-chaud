#!/usr/bin/env bash
# V3 — Voix off masculine publicitaire, découpée en segments courts.
# Des segments courts permettent un montage serré : chaque réplique
# devient un point d'ancrage pour une animation.
set -u
OUT="assets/vo3"
VOICE="am_michael"
SPEED="1.08"
rm -rf "$OUT"; mkdir -p "$OUT"

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
echo "--- Voix off $VOICE / fr-fr / vitesse $SPEED ---"
for entry in "${SEG[@]}"; do
  id="${entry%%|*}"; txt="${entry#*|}"
  f="$OUT/seg${id}.wav"
  npx --yes hyperframes@0.7.87 tts "$txt" --voice "$VOICE" --lang fr-fr --speed "$SPEED" -o "$f" >/dev/null 2>&1
  if [ -f "$f" ]; then
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
    TOTAL=$(python3 -c "print(round($TOTAL + $d, 3))")
    printf "seg%s  %6.2fs  %s\n" "$id" "$d" "$txt"
  else
    printf "seg%s  ÉCHEC\n" "$id"
  fi
done
echo "------------------------------------------------"
echo "TOTAL parole = ${TOTAL}s"
