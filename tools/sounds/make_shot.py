"""Make the gun's sounds without downloads (2026-11-17, first step of the pistol): shot.wav - a
crack of noise over a low thump with a short tail - and dry.wav, the click of an empty gun.

    python tools/sounds/make_shot.py      -> assets/sounds/shot.wav, dry.wav

Placeholders made from numbers: nobody has listened to them yet. A recorded CC0 gunshot should
replace shot.wav in the sound pass.
"""
import math
import random
import struct
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from sound import SOUNDS  # noqa: E402

RATE = 22050


def save(name, samples):
    peak = max(1e-6, max(abs(v) for v in samples))
    with wave.open(str(SOUNDS / f"{name}.wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(b"".join(struct.pack("<h", int(v / peak * 30000)) for v in samples))


def shot():
    rng = random.Random(7)
    out, low = [], 0.0
    for i in range(int(RATE * 0.45)):
        t = i / RATE
        crack = rng.uniform(-1, 1) * math.exp(-t * 38)                    # the sharp front
        low += (rng.uniform(-1, 1) - low) * 0.08                           # low-passed noise: the body
        body = low * 3.0 * math.exp(-t * 9)
        thump = math.sin(2 * math.pi * (95 - 60 * t) * t) * math.exp(-t * 14)
        out.append(crack + body + thump * 0.9)
    return out


def dry():
    rng = random.Random(3)
    return [rng.uniform(-1, 1) * math.exp(-(i / RATE) * 260) * (1 if i < RATE * 0.004 or i > RATE * 0.02 else 0.2)
            for i in range(int(RATE * 0.06))]


if __name__ == "__main__":
    save("shot", shot())
    save("dry", dry())
    print("saved shot.wav, dry.wav in", SOUNDS)
