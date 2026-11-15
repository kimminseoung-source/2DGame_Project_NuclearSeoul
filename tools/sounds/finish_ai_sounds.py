"""Tidy the AI-made sounds (assets/sounds/ai_*.wav) for the game: report their level and silence,
normalise the peak, fade the ends, and make the ambience loops seamless with a crossfade.
Runs in the AI sound environment (needs numpy, soundfile)."""
from pathlib import Path

import numpy as np
import soundfile

SOUNDS = Path(__file__).resolve().parents[2] / "assets" / "sounds"
LOOPS = {"ai_wind_ruins", "ai_subway_tunnel"}
for path in sorted(SOUNDS.glob("ai_*.wav")):
    a, rate = soundfile.read(path, dtype="float32")
    if a.ndim > 1:
        a = a.mean(axis=1)
    rms = float(np.sqrt(np.mean(a ** 2)))
    frame = rate // 20
    quiet = np.mean([np.sqrt(np.mean(a[i:i + frame] ** 2)) < 0.01 for i in range(0, len(a) - frame, frame)])
    zc = float(np.mean(np.abs(np.diff(np.sign(a))) > 0)) * rate / 2      # rough brightness (Hz)
    a = a / max(1e-6, np.max(np.abs(a))) * 0.89                          # peak -1 dB
    if path.stem in LOOPS:                                               # crossfade the end into the start
        n = rate // 2
        fade = np.linspace(0, 1, n, dtype=np.float32)
        a = np.concatenate([a[n:-n], a[-n:] * (1 - fade) + a[:n] * fade])
    else:
        n = rate // 100
        a[:n] *= np.linspace(0, 1, n)
        a[-n * 5:] *= np.linspace(1, 0, n * 5)
    soundfile.write(path, a, rate, subtype="PCM_16")
    print(f"{path.stem:20s} {len(a) / rate:4.1f}s  rms {rms:.3f}  silent {quiet * 100:3.0f}%  brightness ~{zc:5.0f}Hz")
