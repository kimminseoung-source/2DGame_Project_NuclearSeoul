"""How long an idle infected facing the hero takes to spot him by sight alone (no noise)."""
import sys, random; sys.path.insert(0, "src")
from math import atan2
import infected


class H:                                   # a stand-in hero, out in the open
    def __init__(self, moving, sneaking=False):
        self.x, self.y, self.dead, self.roll, self.slash = 0.0, 0.0, False, 0, None
        self.moving, self.sneaking = moving, sneaking
    noticeability = __import__("hero").Hero.noticeability


import area
area.BLOCKS[:] = []
infected.blocks_between = lambda *a, **k: []
for label, h in (("가만히", H(False)), ("살금", H(True, True)), ("걷기", H(True))):
    row = []
    for dist in (40, 60, 100, 150, 200, 250):
        times = []
        for seed in range(200):
            random.seed(seed)
            z = infected.Zombie.__new__(infected.Zombie)
            z.x, z.y, z.state, z.heading = dist, 0.0, "idle", atan2(0 - 0, 0 - dist)
            t = 0.0
            while t < 30:
                if z.sees(h):
                    rate = infected.SPOT_RATE * max(0.0, 1 - dist / infected.SIGHT_RANGE) * h.noticeability()
                    rate *= infected.SPOT_IDLE
                    if dist <= infected.SPOT_SURE or random.random() < rate / 60:
                        break
                t += 1 / 60
            times.append(t)
        times.sort()
        row.append(f"{dist}:{times[len(times) // 2]:.1f}s")
    print(label, " ".join(row))
