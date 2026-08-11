#!/usr/bin/env python3
"""Cale le script sur la voix off, par le compte de syllabes.

Méthode retenue après la première vidéo : la transcription est
impossible ici (Whisper inaccessible), donc on détecte les phrases par
les silences, on traite la parole comme un ruban continu, et on y
projette le script au prorata des syllabes.

Contrôle de justesse : le débit en syllabes par seconde doit rester à
peu près constant d'une réplique à l'autre.
"""
import json, re, subprocess, pathlib

SRC = pathlib.Path("assets/voix.mp3")

# Découpage aligné sur la construction validée avec le client.
LINES = [
    "Vous êtes à Korofina-Nord",
    "et vous cherchez une bonne école pour votre enfant ?",
    "Ne cherchez plus loin.",
    "Vous êtes au bon endroit.",
    "Au Complexe Scolaire Diawoye Kanté,",
    "nous plaçons chaque enfant au cœur de notre mission.",
    "Une éducation de qualité.",
    "La discipline et les valeurs.",
    "Une innovation pédagogique grâce à nos partenariats.",
    "Un accompagnement personnalisé.",
    "Tout est pensé pour permettre à chaque élève de développer son potentiel,",
    "de progresser et d'atteindre son meilleur niveau.",
    "Les inscriptions sont ouvertes !",
    "Nous sommes situés à Korofina-Nord, près de la pharmacie Fady.",
    "Contactez-nous au 74 45 45 71 ou au 93 59 92 01.",
    "CSDK — Apprendre aujourd'hui, réussir demain.",
]

# Les nombres se comptent en toutes lettres, sinon la réplique des
# téléphones est massivement sous-estimée.
NUM = {"74": 4, "45": 3, "71": 4, "93": 4, "59": 3, "92": 4, "01": 3}

def syll(t):
    n = 0
    for tok in re.findall(r"\d+|[^\W\d_]+", t.lower()):
        n += NUM.get(tok, 0) if tok.isdigit() else \
             len(re.findall(r"[aeiouyàâäéèêëîïôöùûüœ]+", tok))
    return max(1, n)

def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())

TOTAL = dur(SRC)

# --- phrases réelles, par détection de silences ---
r = subprocess.run(["ffmpeg", "-i", str(SRC), "-af",
                    "silencedetect=noise=-35dB:d=0.25", "-f", "null", "-"],
                   capture_output=True, text=True)
st = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
en = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", r.stderr)]

ph, cur = [], 0.0
for a, b in zip(st, en + [TOTAL]):
    if a - cur > 0.15:
        ph.append((cur, a))
    cur = b
if TOTAL - cur > 0.15:
    ph.append((cur, TOTAL))
speech = sum(b - a for a, b in ph)

def wall(pos):
    """Position dans le ruban de parole (0..1) → instant réel."""
    want, acc = pos * speech, 0.0
    for a, b in ph:
        d = b - a
        if acc + d >= want:
            return round(a + (want - acc), 3)
        acc += d
    return round(ph[-1][1], 3)

S = [syll(l) for l in LINES]
TOT = sum(S)

print(f"Audio    {TOTAL:.2f}s · parole {speech:.2f}s · {len(ph)} phrases")
print(f"Script   {len(LINES)} répliques · {TOT} syllabes · "
      f"{TOT/speech:.2f} syll/s\n")

segs, cum = [], 0.0
for txt, n in zip(LINES, S):
    a = wall(cum / TOT); cum += n; b = wall(cum / TOT)
    segs.append({"id": len(segs) + 1, "text": txt,
                 "start": a, "end": b, "dur": round(b - a, 3)})
    print(f"{segs[-1]['id']:2d}  {a:6.2f} → {b:6.2f}  ({b-a:4.2f}s)  {txt[:44]}")

bad = [s["id"] for x, s in zip(segs, segs[1:]) if s["start"] < x["end"] - 0.01]
print(f"\nChevauchements : {bad if bad else 'aucun'}")

pathlib.Path("timeline.json").write_text(json.dumps(
    {"audio": SRC.name, "duration": round(TOTAL, 3), "segments": segs},
    indent=1, ensure_ascii=False))
