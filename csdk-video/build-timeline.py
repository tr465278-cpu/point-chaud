#!/usr/bin/env python3
"""Cale les répliques sur la grille musicale et écrit timeline.json.

Le montage est construit à 120 BPM : un temps toutes les 0,5 s. Chaque
réplique démarre sur un temps, ce qui garantit que les coupes tombent
avec la musique plutôt qu'à côté.
"""
import json, subprocess, pathlib

BPM = 120.0
BEAT = 60.0 / BPM          # 0.5 s
LEAD = 1.0                 # amorce avant la première réplique (2 temps)
VO = pathlib.Path("assets/vo3")

def dur(p):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return float(out.stdout.strip())

# Respiration voulue après chaque réplique, en temps (0,5 s chacun).
# Une valeur plus élevée = respiration narrative avant un changement de ton.
GAP_BEATS = {
    1: 1,   2: 0,   3: 0,   4: 0,   5: 0,   6: 1,   7: 1,   8: 0,
    9: 1,  10: 0,  11: 0,  12: 1,  13: 0,  14: 1,  15: 0,  16: 1,
    17: 0, 18: 0,  19: 0,
}

def snap_up(t):
    """Repousse t sur le prochain temps de la grille."""
    n = t / BEAT
    return (int(n) + (0 if abs(n - round(n)) < 1e-6 else 1)) * BEAT

segs, cursor = [], LEAD
for i in range(1, 20):
    f = VO / f"seg{i:02d}.wav"
    d = dur(f)
    start = snap_up(cursor)
    segs.append({"id": i, "file": str(f), "start": round(start, 3),
                 "dur": round(d, 3), "end": round(start + d, 3)})
    cursor = start + d + GAP_BEATS[i] * BEAT

TAIL = 2.0   # respiration finale sur le logo
# La durée totale est arrondie à la mesure pleine : la musique se
# termine sur un temps fort plutôt qu'en cours de mesure.
BAR = BEAT * 4
raw = segs[-1]["end"] + TAIL
total = ((int(raw / BAR) + (0 if abs(raw / BAR - round(raw / BAR)) < 1e-6 else 1)) * BAR)

data = {"bpm": BPM, "beat": BEAT, "lead": LEAD,
        "total": round(total, 3), "segments": segs}
pathlib.Path("timeline.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

print(f"BPM {BPM:.0f} · temps {BEAT}s · {len(segs)} répliques")
for s in segs:
    print(f"  seg{s['id']:02d}  {s['start']:6.2f} → {s['end']:6.2f}  ({s['dur']:.2f}s)")
print(f"\nDURÉE TOTALE = {total:.2f}s  ({total/BEAT:.0f} temps, {total/(BEAT*4):.0f} mesures)")
