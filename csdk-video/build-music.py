#!/usr/bin/env python3
"""Compose le lit musical du spot : 120 BPM, la mineur, 27 mesures.

La piste est synthétisée sur la même grille que le montage, donc chaque
coupe à l'image tombe sur un temps. La structure suit la narration :
elle s'ouvre en retenue, monte à l'énumération des métiers, s'installe
sur la présentation de l'école, puis culmine sur l'appel à l'action.
"""
import numpy as np, soundfile as sf, json, pathlib

SR = 48000
BPM = 120.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
TOTAL = json.loads(pathlib.Path("timeline.json").read_text())["total"]
N = int(TOTAL * SR)
t = np.arange(N) / SR

def env(start, dur, attack, decay, curve=2.0):
    """Enveloppe percussive : attaque courte, décroissance exponentielle."""
    e = np.zeros(N)
    i0 = int(start * SR); i1 = min(int((start + dur) * SR), N)
    if i1 <= i0: return e
    n = i1 - i0
    a = max(1, int(attack * SR))
    seg = np.ones(n)
    seg[:min(a, n)] = np.linspace(0, 1, min(a, n))
    d = np.linspace(0, 1, n) ** curve
    seg *= np.exp(-d * decay)
    e[i0:i1] = seg
    return e

def sine(f, phase=0.0):
    return np.sin(2 * np.pi * f * t + phase)

def noise(seed):
    return np.random.default_rng(seed).normal(0, 1, N)

# ---------------------------------------------------------------- sections
# (mesure_debut, mesure_fin, intensité 0..1) — pilote la densité
SECTIONS = [
    (0,  2, 0.25),   # amorce : le rêve
    (2,  5, 0.55),   # les métiers s'enchaînent
    (5,  7, 0.70),   # le bon départ
    (7, 13, 0.80),   # l'école
    (13, 17, 0.90),  # les trois piliers
    (17, 21, 0.85),  # l'environnement
    (21, 25, 1.00),  # logo + contacts : plein régime
    (25, 27, 0.70),  # sortie
]
def intensity(bar):
    for a, b, v in SECTIONS:
        if a <= bar < b: return v
    return 0.6

# ---------------------------------------------------------------- harmonie
# La mineur : Am – F – C – G, une mesure chacun.
ROOTS = [110.00, 87.31, 130.81, 98.00]          # A2  F2  C3  G2
TRIADS = [[220.0, 261.63, 329.63],              # Am  A4 C5 E5
          [174.61, 220.0, 261.63],              # F   F4 A4 C5
          [261.63, 329.63, 392.0],              # C   C5 E5 G5
          [196.0, 246.94, 293.66]]              # G   G4 B4 D5

nbars = int(TOTAL / BAR)
kick = np.zeros(N); bass = np.zeros(N); arp = np.zeros(N)
hat  = np.zeros(N); pad  = np.zeros(N); fx = np.zeros(N)

for b in range(nbars):
    t0 = b * BAR
    inten = intensity(b)
    ci = b % 4
    root = ROOTS[ci]
    triad = TRIADS[ci]

    # --- Kick : quatre au sol dès que ça démarre
    if inten >= 0.5:
        for k in range(4):
            s = t0 + k * BEAT
            # descente de hauteur = "punch" caractéristique
            pitch = 110 * np.exp(-np.linspace(0, 1, N) * 0)  # placeholder
            kick += env(s, 0.28, 0.002, 7.0) * np.sin(
                2 * np.pi * (52 + 60 * np.exp(-(t - s).clip(0) * 28)) * (t - s).clip(0))
    elif inten >= 0.25:
        for k in (0, 2):
            s = t0 + k * BEAT
            kick += env(s, 0.30, 0.002, 6.0) * np.sin(
                2 * np.pi * (50 + 55 * np.exp(-(t - s).clip(0) * 26)) * (t - s).clip(0))

    # --- Basse : croches syncopées
    for k in range(8):
        s = t0 + k * (BEAT / 2)
        if k % 2 == 0 or inten >= 0.8:
            amp = 0.55 if k % 2 == 0 else 0.3
            bass += amp * env(s, BEAT * 0.55, 0.006, 3.2) * (
                0.8 * sine(root) + 0.2 * sine(root * 2))

    # --- Arpège : doubles-croches, timbre pincé
    if inten >= 0.5:
        for k in range(16):
            s = t0 + k * (BEAT / 4)
            f = triad[k % 3] * (2 if (k // 3) % 2 else 1)
            arp += 0.22 * inten * env(s, 0.20, 0.003, 9.0) * (
                0.7 * sine(f) + 0.3 * sine(f * 2.01))

    # --- Charleston : contretemps
    if inten >= 0.55:
        for k in range(8):
            s = t0 + k * (BEAT / 2) + BEAT / 4
            hat += 0.16 * inten * env(s, 0.07, 0.001, 14.0) * noise(1000 + b * 8 + k)

    # --- Nappe : tenue harmonique douce
    for f in triad:
        pad += 0.05 * inten * env(t0, BAR, 0.25, 1.2, curve=1.0) * sine(f / 2)

# --- Risers avant chaque changement de section
for a, _, _ in SECTIONS[1:]:
    s = max(0.0, a * BAR - BAR)          # une mesure de montée
    e = env(s, BAR, 0.9, 0.4, curve=1.0)
    sweep = np.sin(2 * np.pi * (200 + 2600 * np.clip((t - s) / BAR, 0, 1) ** 2) * t)
    fx += 0.10 * e * (0.5 * sweep + 0.5 * noise(7 + a) * 0.5)

# --- Impact grave sur chaque début de section
for a, _, _ in SECTIONS[1:]:
    s = a * BAR
    fx += 0.5 * env(s, 1.2, 0.002, 4.0) * np.sin(
        2 * np.pi * (44 + 40 * np.exp(-(t - s).clip(0) * 12)) * (t - s).clip(0))

# ---------------------------------------------------------------- mixage
mix = (0.95 * kick + 0.60 * bass + 0.40 * arp +
       0.28 * hat + 0.45 * pad + 0.55 * fx)

# Fondu d'entrée, fondu de sortie
fi = int(0.6 * SR); fo = int(1.8 * SR)
mix[:fi] *= np.linspace(0, 1, fi)
mix[-fo:] *= np.linspace(1, 0, fo)

# Compression douce + limiteur, pour une piste dense mais tenue
mix = np.tanh(mix * 1.25) * 0.82
mix /= max(1e-9, np.abs(mix).max()) / 0.89

stereo = np.stack([mix, np.roll(mix, 90)], axis=1)   # légère largeur stéréo
pathlib.Path("assets/bgm").mkdir(parents=True, exist_ok=True)
sf.write("assets/bgm/musique.wav", stereo, SR)
print(f"Musique écrite : {TOTAL:.2f}s · {nbars} mesures · {BPM:.0f} BPM · la mineur")
