"""Sound effects (assets/sounds/, made by tools/sounds/make_sfx.py).

`play(name, volume, at)` plays one effect; with `at` (a position on the ground) it gets quieter
with distance from the listener (the hero), so an infected growling behind a wreck is still
heard - the sound is the clue for what the facing vision hides. Missing audio never stops the
game: if the device or a file is unavailable the call does nothing.
"""

from math import hypot

import pico2d
from sdl2 import sdlmixer

from settings import ROOT

SOUNDS = ROOT / "assets" / "sounds"
HEAR_RANGE = 420           # px: beyond this an effect at a position is silent
MASTER = 0.8


class Sounds:
    def __init__(self):
        self.wavs = {}
        self.listener = (0.0, 0.0)
        for path in sorted(SOUNDS.glob("*.wav")):
            try:
                self.wavs[path.stem] = pico2d.load_wav(str(path))
            except Exception:              # no audio device: play silently
                pass

    def play(self, name, volume=1.0, at=None):
        wav = self.wavs.get(name)
        if wav is None:
            return
        if at is not None:
            dist = hypot(at[0] - self.listener[0], at[1] - self.listener[1])
            volume *= max(0.0, 1 - dist / HEAR_RANGE) ** 1.5
        level = round(128 * MASTER * min(1.0, volume))
        if level <= 0:
            return
        channel = sdlmixer.Mix_PlayChannel(-1, wav.wav, 0)
        if channel >= 0:
            sdlmixer.Mix_Volume(channel, level)
