#!/usr/bin/env bash
# Génère la voix off française segment par segment et mesure chaque durée.
set -u
OUT="assets/vo"
mkdir -p "$OUT"

declare -a SEG=(
  "01|Chaque enfant porte un rêve."
  "02|Un rêve de devenir médecin, enseignant, ingénieur, artiste ou entrepreneur."
  "03|Mais tous les grands rêves ont besoin d'un bon départ."
  "04|Au Complexe Scolaire Diawoye Kanté, nous croyons qu'une éducation de qualité peut changer une vie."
  "05|Ici, vos enfants apprennent avec discipline, grandissent avec confiance et avancent vers la réussite."
  "06|Offrez à votre enfant un environnement où il pourra apprendre, s'épanouir et construire son avenir."
  "07|Complexe Scolaire Diawoye Kanté. Apprendre aujourd'hui, réussir demain."
  "08|Nous sommes situés à Korofina-Nord, près de la pharmacie Fady."
  "09|Appelez-nous au 74 45 45 71 ou au 93 59 92 01."
  "10|Les inscriptions sont ouvertes."
)

SPEED="${1:-1.0}"
TOTAL=0
echo "--- Voix off ff_siwis / fr-fr / vitesse ${SPEED} ---"
for entry in "${SEG[@]}"; do
  id="${entry%%|*}"
  txt="${entry#*|}"
  f="$OUT/seg${id}.wav"
  npx --yes hyperframes@0.7.87 tts "$txt" --voice ff_siwis --lang fr-fr --speed "$SPEED" -o "$f" >/dev/null 2>&1
  if [ -f "$f" ]; then
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
    TOTAL=$(python3 -c "print(round($TOTAL + $d, 2))")
    printf "seg%s  %6.2fs  %s\n" "$id" "$d" "$txt"
  else
    echo "seg$id  ÉCHEC"
  fi
done
echo "-----------------------------------------------"
echo "TOTAL parole = ${TOTAL}s (hors respirations)"
