"""Fixed spot distance: in sight and this close -> "!" at once, farther -> never."""
import sys; sys.path.insert(0, "src")
from math import pi
import infected
infected.blocks_between = lambda *a, **k: []


class H:
    def __init__(self, moving, sneaking=False):
        self.x, self.y, self.dead, self.roll, self.slash = 0.0, 0.0, False, 0, None
        self.moving, self.sneaking = moving, sneaking


def spotted(h, dist, facing=True):
    z = infected.Zombie.__new__(infected.Zombie)
    z.x, z.y, z.heading = dist, 0.0, pi if facing else 0.0
    return z.sees(h) and dist <= infected.SPOT_DIST


for label, h in (("걷기", H(True)), ("가만히", H(False)), ("살금", H(True, True))):
    print(label, {d: spotted(h, d) for d in (30, 95, 135, 145, 250)}, "| 등 돌림 100:", spotted(h, 100, False), "30:", spotted(h, 30, False))
