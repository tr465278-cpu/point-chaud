#!/usr/bin/env python3
"""Aligne le script sur la voix off ElevenLabs.

La transcription est impossible (modèle Whisper inaccessible depuis cet
environnement). L'alignement se fait donc par la durée : on détecte les
phrases à l'oreille de la machine — les silences — puis on y projette le
script au prorata de la longueur de chaque réplique.

La référence de longueur est la version Kokoro déjà générée : elle a été
lue mot pour mot à partir du même script, donc ses durées relatives sont
un bon modèle du débit attendu.
"""
import json, re, subprocess, pathlib

SRC = next(pathlib.Path("assets/voix-off").glob("*.mp3"))
LINES = [
    "Chaque enfant porte un rêve.",
    "Devenir médecin.", "Enseignante.", "Ingénieur.", "Artiste.", "Entrepreneur.",
    "Mais tous les grands rêves ont besoin d'un bon départ.",
    "Au Complexe Scolaire Diawoye Kanté,",
    "nous croyons qu'une éducation de qualité peut changer une vie.",
    "Ici, vos enfants apprennent avec discipline.",
    "Grandissent avec confiance.",
    "Et avancent vers la réussite.",
    "Offrez à votre enfant un environnement pour apprendre,",
    "s'épanouir, et construire son avenir.",
    "Complexe Scolaire Diawoye Kanté.",
    "Apprendre aujourd'hui, réussir demain.",
    "Korofina-Nord, près de la pharmacie Fady.",
    "Appelez-nous au 74 45 45 71, ou au 93 59 92 01.",
    "Les inscriptions sont ouvertes !",
]

def probe_duration(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())

TOTAL_AUDIO = probe_duration(SRC)

# ---- 1. Détection des phrases ------------------------------------------
r = subprocess.run(["ffmpeg", "-i", str(SRC), "-af",
                    "silencedetect=noise=-35dB:d=0.28", "-f", "null", "-"],
                   capture_output=True, text=True)
starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
ends   = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", r.stderr)]

phrases, cur = [], 0.0
for s, e in zip(starts, ends + [TOTAL_AUDIO]):
    if s - cur > 0.15:
        phrases.append((round(cur, 3), round(s, 3)))
    cur = e
if TOTAL_AUDIO - cur > 0.15:
    phrases.append((round(cur, 3), round(TOTAL_AUDIO, 3)))

speech = sum(b - a for a, b in phrases)

# ---- 2. Référence de longueur (Kokoro, même script) --------------------
ref = []
for i in range(1, 20):
    f = pathlib.Path(f"assets/vo3/seg{i:02d}.wav")
    ref.append(probe_duration(f) if f.exists() else len(LINES[i - 1]) * 0.055)
ref_total = sum(ref)

print(f"Fichier      {SRC.name}")
print(f"Durée        {TOTAL_AUDIO:.2f}s · parole {speech:.2f}s · {len(phrases)} phrases")
print(f"Référence    {ref_total:.2f}s de parole sur le même script")
print(f"Écart        {abs(speech - ref_total) / ref_total * 100:.1f}%\n")

# ---- 3. Projection du script sur les phrases ---------------------------
# Chaque réplique reçoit la phrase dont le centre est le plus proche de sa
# position attendue, calculée au prorata dans le flux de parole.
cum, marks = 0.0, []
for d in ref:
    marks.append((cum + d / 2) / ref_total)      # centre relatif attendu
    cum += d

def to_wall(pos):
    """Convertit une position dans le flux de parole (0..1) en instant réel.

    On marche le long des phrases en ignorant les silences : la parole est
    traitée comme un ruban continu, ce qui reste juste même quand la
    lectrice groupe plusieurs répliques dans une seule respiration.
    """
    want, acc = pos * speech, 0.0
    for a, b in phrases:
        d = b - a
        if acc + d >= want:
            return round(a + (want - acc), 3)
        acc += d
    return round(phrases[-1][1], 3)

# Bornes cumulées de chaque réplique dans le ruban de parole.
bounds, cum = [], 0.0
for d in ref:
    bounds.append((cum / ref_total, (cum + d) / ref_total))
    cum += d

segments = []
for i, (p0, p1) in enumerate(bounds):
    a, b = to_wall(p0), to_wall(p1)
    segments.append({"id": i + 1, "text": LINES[i],
                     "start": a, "end": b, "dur": round(b - a, 3)})

for s in segments:
    print(f"  {s['id']:02d}  {s['start']:6.2f} → {s['end']:6.2f}  "
          f"({s['dur']:4.2f}s)  {s['text'][:44]}")

# Contrôle : aucune réplique ne doit se chevaucher ni reculer.
bad = [s["id"] for a, s in zip(segments, segments[1:]) if s["start"] < a["end"] - 0.01]
print(f"\nChevauchements : {bad if bad else 'aucun'}")

BEAT, BAR = 0.5, 2.0
total = ((int((TOTAL_AUDIO + 1.2) / BAR) + 1) * BAR)
pathlib.Path("timeline.json").write_text(json.dumps(
    {"source": SRC.name, "bpm": 120.0, "beat": BEAT, "lead": 0.0,
     "audio_duration": round(TOTAL_AUDIO, 3), "total": round(total, 3),
     "segments": segments}, indent=2, ensure_ascii=False))
print(f"DURÉE TOTALE = {total:.2f}s ({total / BAR:.0f} mesures)")
