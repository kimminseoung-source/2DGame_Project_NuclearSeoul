"""People at the station (2026-11-18 "역에 가면 군인, 민간인들이 있다는 설정", "작게 만들어 보고"):
soldiers who shoot the infected from where they stand, civilians who huddle and wait for the train.

Both are bodies the infected can spot, chase and claw like the hero (infected.update takes any
"prey" with x, y, dead, moving, sneaking, roll, slash). One that falls rises a little later as an
infected - from inside the defended spot. KINDS holds each kind's numbers, so a new kind is one row.
"""

import random
from math import cos, hypot, sin, tau

import area
import ui
from vision_cone import ray_hit

# kind: (name, health in blows, tint of the borrowed hero sprite, gun or None)
KINDS = {
    "soldier": ("군인", 3, (190, 225, 170), {"range": 300.0, "every": (0.9, 1.4), "rounds": 12,
                                           "hit": 0.5, "damage": (6, 9), "noise": 400}),
    "civilian": ("시민", 2, (215, 220, 255), None),
}
RISE_TIME = 2.5          # s from falling to getting up as an infected


class Survivor:
    moving, sneaking, roll, slash = False, False, 0.0, None      # what an infected's eyes read

    def __init__(self, kind, x, y, facing=1):
        self.kind = kind
        self.name, self.blows, self.tint, gun = KINDS[kind]
        self.gun = dict(gun) if gun else None
        self.x, self.y, self.facing = float(x), float(y), facing
        self.dead = 0.0              # s since it fell (0 = alive)
        self.risen = False
        self.cooldown = random.uniform(0.3, 1.0)
        self.time = 0.0
        self.hurt_flash = 0.0

    @property
    def alive(self):
        return not self.dead

    def take_blow(self):
        """An infected's claw lands. True if it fell."""
        self.blows -= 1
        self.hurt_flash = 0.2
        if self.blows <= 0 and not self.dead:
            self.dead = 0.001
            return True
        return False

    def update(self, dt, game):
        """Returns ("shot", target, hit) when a soldier fires, ("rise",) when a fallen one gets up."""
        self.time += dt
        self.hurt_flash = max(0.0, self.hurt_flash - dt)
        if self.dead:
            self.dead += dt
            if self.dead >= RISE_TIME and not self.risen:
                self.risen = True
                return ("rise",)
            return None
        if not self.gun or self.gun["rounds"] <= 0:
            return None
        self.cooldown -= dt
        if self.cooldown > 0:
            return None
        target = self.nearest_target(game)
        if target is None:
            return None
        self.cooldown = random.uniform(*self.gun["every"])
        self.gun["rounds"] -= 1
        self.facing = 1 if target.x >= self.x else -1
        return ("shot", target, random.random() < self.gun["hit"])

    def nearest_target(self, game):
        best, best_d = None, self.gun["range"]
        for z in game.zombies:
            if not z.alive:
                continue
            d = hypot(z.x - self.x, z.y - self.y)
            if d > best_d or d < 1:
                continue
            ux, uy = (z.x - self.x) / d, (z.y - self.y) / d
            if ray_hit(self.x, self.y, ux, uy, area.blocks_between(self.x, self.y, z.x, z.y, sight=True)) < d:
                continue                                   # a wall in the way
            best, best_d = z, d
        return best

    def draw(self, look, cx, cy):
        x, y = self.x - cx, self.y - cy
        r, g, b = (255, 120, 120) if self.hurt_flash > 0 else self.tint
        if self.dead:
            look.draw("down", min(1.0, self.dead * 1.5), x, y, self.facing, tint=(r // 2, g // 2, b // 2))
        else:
            look.draw("idle", self.time, x, y, self.facing, tint=(r, g, b))
            ui.world_text_center(x, y + 64, self.name, (210, 230, 200) if self.gun else (210, 215, 240), 11)


def place(kind, near):
    """A free spot for one survivor around `near` (x, y), clear of walls and wrecks."""
    nx, ny = near
    for radius in range(0, 240, 12):
        for step in range(12):
            a = step / 12 * tau + radius
            x, y = nx + radius * cos(a), ny + radius * sin(a)
            if not area.blocked(x, y, 14):
                return Survivor(kind, x, y, 1 if x < nx else -1)
    return Survivor(kind, nx, ny)



def damage_of(gun):
    return random.randint(*gun["damage"])
