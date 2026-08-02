#!/usr/bin/env python3
"""Mixe le master audio : voix off + musique duckée + bruitages.

Écrit aussi sfx.json, la liste des évènements sonores avec leur instant
exact — le montage vidéo s'y accroche pour que chaque bruitage tombe
sur son animation.
"""
import numpy as np, soundfile as sf, json, pathlib, subprocess

SR = 48000
TL = json.loads(pathlib.Path("timeline.json").read_text())
TOTAL, BEAT = TL["total"], TL["beat"]
N = int(TOTAL * SR)
SFX_DIR = pathlib.Path(".claude/skills/media-use/audio/assets/sfx")

def load(path, target_sr=SR):
    """Charge un fichier audio en mono à la fréquence du master."""
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1",
         "-ar", str(target_sr), "-f", "f32le", "-"],
        capture_output=True)
    return np.frombuffer(out.stdout, dtype=np.float32).copy()

def place(buf, sig, at, gain=1.0):
    i0 = int(at * SR)
    i1 = min(i0 + len(sig), len(buf))
    if i1 > i0:
        buf[i0:i1] += sig[:i1 - i0] * gain

# ------------------------------------------------------------------ voix
# Piste unique : la voix ElevenLabs est conservée telle quelle, avec ses
# respirations d'origine. Ré-espacer les répliques casserait la
# performance de la lectrice.
voice = np.zeros(N)
src = next(pathlib.Path("assets/voix-off").glob("*.mp3"))
place(voice, load(src), 0.0)

# ------------------------------------------------------------ bruitages
# Chaque réplique est précédée d'un whoosh : l'oreille anticipe la coupe.
WHOOSH = ["whoosh-short.mp3", "whoosh.mp3", "whoosh-cinematic.mp3"]
events = []
for i, s in enumerate(TL["segments"]):
    if i == 0:
        continue                      # pas de whoosh avant la toute première réplique
    events.append({"at": round(max(0.0, s["start"] - 0.20), 3),
                   "file": WHOOSH[i % 3], "gain": 0.38, "role": "transition"})

# Impacts graves aux ruptures de section (les mêmes que la musique).
for bar in (2, 5, 7, 13, 17, 21, 25):
    events.append({"at": round(bar * BEAT * 4, 3),
                   "file": "impact-bass-1.mp3", "gain": 0.50, "role": "section"})

# Ponctuations : les métiers claquent, le logo scintille, le final frappe.
for s in TL["segments"]:
    if s["id"] in (2, 3, 4, 5, 6):
        events.append({"at": s["start"], "file": "pop.mp3", "gain": 0.40, "role": "mot"})
    if s["id"] in (10, 11, 12):
        events.append({"at": s["start"], "file": "click.mp3", "gain": 0.34, "role": "pilier"})
events += [
    {"at": TL["segments"][14]["start"] - 1.0, "file": "riser.mp3",      "gain": 0.42, "role": "montée"},
    {"at": TL["segments"][14]["start"],       "file": "sparkle.mp3",    "gain": 0.52, "role": "logo"},
    {"at": TL["segments"][14]["start"] + .05, "file": "impact-bass-2.mp3","gain": 0.55, "role": "logo"},
    {"at": TL["segments"][17]["start"],       "file": "chime.mp3",      "gain": 0.34, "role": "contact"},
    {"at": TL["segments"][18]["start"] - .9,  "file": "riser.mp3",      "gain": 0.46, "role": "montée"},
    {"at": TL["segments"][18]["start"],       "file": "impact-bass-1.mp3","gain": 0.60, "role": "final"},
    {"at": TL["segments"][18]["start"] + .04, "file": "sparkle.mp3",    "gain": 0.40, "role": "final"},
]
events.sort(key=lambda e: e["at"])

sfx = np.zeros(N)
cache = {}
for e in events:
    f = SFX_DIR / e["file"]
    if not f.exists():
        continue
    if e["file"] not in cache:
        cache[e["file"]] = load(f)
    place(sfx, cache[e["file"]], e["at"], e["gain"])

pathlib.Path("sfx.json").write_text(json.dumps(events, indent=2, ensure_ascii=False))

# ------------------------------------------------------------- musique
mus, msr = sf.read("assets/bgm/musique.wav", dtype="float32")
if mus.ndim > 1:
    mus = mus.mean(axis=1)
mus = np.pad(mus, (0, max(0, N - len(mus))))[:N]

# Ducking : la musique s'efface sous la voix, avec attaque/relâchement
# progressifs pour éviter le pompage.
lvl = np.abs(voice)
win = int(0.05 * SR)
lvl = np.convolve(lvl, np.ones(win) / win, mode="same")
speaking = (lvl > 0.012).astype(np.float32)
smooth = int(0.22 * SR)
speaking = np.convolve(speaking, np.ones(smooth) / smooth, mode="same").clip(0, 1)
duck = 1.0 - 0.62 * speaking          # -8 dB environ sous la voix

# ------------------------------------------------------------- master
mix = 1.00 * voice + 0.34 * (mus * duck) + 0.85 * sfx
mix = np.tanh(mix * 1.1) * 0.9
mix /= max(1e-9, np.abs(mix).max()) / 0.95

tmp = "assets/_master_raw.wav"
sf.write(tmp, mix, SR)
subprocess.run(["ffmpeg", "-y", "-i", tmp,
                "-af", "loudnorm=I=-14:TP=-1.0:LRA=9",
                "-ar", "48000", "-b:a", "224k",
                "assets/master-audio.mp3"], capture_output=True)
pathlib.Path(tmp).unlink(missing_ok=True)

print(f"Master audio : {TOTAL:.2f}s")
print(f"  voix off   19 répliques")
print(f"  bruitages  {len(events)} évènements")
print(f"  musique    duckée à -8 dB sous la voix")
print(f"  loudness   -14 LUFS (norme réseaux sociaux)")
