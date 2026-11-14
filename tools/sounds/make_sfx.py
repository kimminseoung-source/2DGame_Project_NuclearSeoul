"""Make the game's sound effects from numbers (sfxr-style synthesis, no downloads, our own sounds).

    .venv\\Scripts\\python.exe tools/sounds/make_sfx.py

Writes 16-bit mono 44.1 kHz WAV files into assets/sounds/. Every sound is a short recipe:
an oscillator (sine / square / saw / noise) whose pitch slides, shaped by an attack-hold-decay
envelope and an optional low-pass filter; some sounds mix two layers. The random seed is fixed,
so running it again makes the same files.
"""

import math
import random
import struct
import wave
from pathlib import Path

RATE = 44100
OUT = Path(__file__).resolve().parents[2] / "assets" / "sounds"


def layer(seconds, wave_kind="noise", f0=440.0, f1=None, attack=0.005, hold=0.0, decay=None,
          lowpass=1.0, gain=1.0, vibrato=0.0, vib_rate=0.0, seed=1):
    """One voice: wave_kind oscillator from f0 to f1 Hz with an envelope, filtered."""
    rng = random.Random(seed)
    n = int(seconds * RATE)
    decay = seconds - attack - hold if decay is None else decay
    f1 = f0 if f1 is None else f1
    phase, low, out, noise_val, noise_phase = 0.0, 0.0, [], 0.0, 1.0
    for i in range(n):
        t = i / RATE
        p = i / max(1, n - 1)
        freq = f0 * (f1 / f0) ** p if f0 > 0 and f1 > 0 else f0 + (f1 - f0) * p
        if vibrato:
            freq *= 1 + vibrato * math.sin(2 * math.pi * vib_rate * t)
        phase = (phase + freq / RATE) % 1.0
        if wave_kind == "sine":
            v = math.sin(2 * math.pi * phase)
        elif wave_kind == "square":
            v = 1.0 if phase < 0.5 else -1.0
        elif wave_kind == "saw":
            v = 2 * phase - 1
        else:                                      # noise, re-rolled at the oscillator rate
            noise_phase += freq / RATE
            if noise_phase >= 1.0:
                noise_phase -= 1.0
                noise_val = rng.uniform(-1, 1)
            v = noise_val
        low += lowpass * (v - low)                 # one-pole low-pass (1.0 = off)
        if t < attack:
            env = t / attack
        elif t < attack + hold:
            env = 1.0
        else:
            env = max(0.0, 1 - (t - attack - hold) / max(1e-6, decay)) ** 2
        out.append(low * env * gain)
    return out


def mix(*layers):
    n = max(len(l) for l in layers)
    return [sum(l[i] for l in layers if i < len(l)) for i in range(n)]


def save(name, samples, peak=0.85):
    top = max(1e-6, max(abs(s) for s in samples))
    data = b"".join(struct.pack("<h", int(max(-1, min(1, s / top * peak)) * 32767)) for s in samples)
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(data)
    print("saved", name, f"{len(samples) / RATE:.2f}s")


# What each sound is for (play.py decides when and how loud).
RECIPES = {
    # hero
    "slash": lambda: layer(0.20, "noise", 9000, 1800, attack=0.01, lowpass=0.35, seed=2),            # blade whoosh
    "slash_hit": lambda: mix(layer(0.16, "sine", 140, 55, attack=0.002, gain=1.0),                   # meaty thump
                             layer(0.07, "noise", 6000, 2500, attack=0.001, lowpass=0.6, gain=0.7, seed=3)),
    "hurt": lambda: mix(layer(0.24, "square", 220, 90, attack=0.003, lowpass=0.25, gain=0.6),        # hero is hit
                        layer(0.12, "noise", 3000, 800, attack=0.001, lowpass=0.5, gain=0.8, seed=4)),
    "roll": lambda: layer(0.24, "noise", 2500, 700, attack=0.03, lowpass=0.18, seed=5),              # cloth rush
    "step": lambda: layer(0.06, "noise", 1400, 600, attack=0.002, lowpass=0.2, seed=6),              # footstep
    "grab": lambda: mix(layer(0.30, "saw", 85, 60, attack=0.01, lowpass=0.12, gain=0.9),             # held fast
                        layer(0.10, "noise", 900, 300, attack=0.001, lowpass=0.3, gain=0.8, seed=7)),
    # infected
    "warn": lambda: mix(layer(0.07, "square", 880, 880, attack=0.002, lowpass=0.5, gain=0.5),        # "!" about to strike
                        layer(0.14, "saw", 120, 95, attack=0.01, lowpass=0.15, gain=0.9)),
    "alert": lambda: layer(0.45, "saw", 70, 95, attack=0.05, lowpass=0.08, vibrato=0.08, vib_rate=11),  # "?" low growl
    "infected_down": lambda: mix(layer(0.35, "saw", 110, 45, attack=0.005, lowpass=0.1, gain=0.8),  # falls
                                 layer(0.18, "noise", 700, 200, attack=0.002, lowpass=0.25, gain=0.6, seed=8)),
    "infected_step": lambda: layer(0.08, "noise", 700, 300, attack=0.004, lowpass=0.12, seed=9),    # shuffling feet
    # time crawl (exposure)
    "slow_in": lambda: layer(0.45, "sine", 320, 70, attack=0.01, lowpass=0.6, vibrato=0.03, vib_rate=6),
    "slow_out": lambda: layer(0.30, "sine", 70, 300, attack=0.01, lowpass=0.6),
    "exposure_limit": lambda: mix(layer(0.6, "square", 180, 150, attack=0.005, lowpass=0.2, gain=0.6, vibrato=0.05, vib_rate=18),
                                  layer(0.6, "noise", 4000, 1500, attack=0.01, lowpass=0.3, gain=0.4, seed=10)),
}


if __name__ == "__main__":
    for name, recipe in RECIPES.items():
        save(name, recipe())
