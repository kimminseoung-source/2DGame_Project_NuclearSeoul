"""Ranged infected prototype: authored key poses, independent glow, interruptible tell.

The alley mixes a few in (play.Game.new_arrival, 2026-11-26); the station defense never gets one.
tools/run_spitter_trial.py is the isolated trial.
"""
from math import atan2, cos, hypot, sqrt
from pathlib import Path

import pico2d
import ui
from area import near_blocks
from infected import Zombie
from settings import DOT, ROOT

WINDUP, RELEASE, RECOVER = .8, .16, 1.2
SHOT_SPEED, SHOT_RANGE, SHOT_DAMAGE = 180.0, 440.0, 12
ATTACK_RANGE = 230.0
ART = ROOT / 'assets/characters/previews/spitter_trial_v1'


def ray_rect_entry(x, y, ux, uy, rect):
    """Entry distance, including a start inside a wall (vision ray_hit returns EXIT)."""
    near, far = 0., float('inf')
    for p, u, lo, hi in ((x, ux, rect[0], rect[2]), (y, uy, rect[1], rect[3])):
        if abs(u) < 1e-9:
            if not lo <= p <= hi:
                return float('inf')
        else:
            a, b = (lo - p) / u, (hi - p) / u
            near, far = max(near, min(a, b)), min(far, max(a, b))
    return near if near <= far else float('inf')


def ray_circle_entry(x, y, ux, uy, cx, cy, radius):
    dx, dy = cx - x, cy - y
    along = dx * ux + dy * uy
    disc = radius * radius - (dx * dx + dy * dy - along * along)
    if dx * dx + dy * dy <= radius * radius:
        return 0.
    if disc < 0 or along < 0:
        return float('inf')
    return max(0., along - sqrt(disc))


class SpitShot:
    radius = 3.

    def __init__(self, owner, aim):
        self.owner = owner
        self.x = owner.x + (owner.facing * 16 if getattr(owner, 'ranged', False) else 0.)
        self.y = owner.y
        dx, dy = aim[0] - self.x, aim[1] - self.y
        length = hypot(dx, dy) or 1.
        self.ux, self.uy = dx / length, dy / length
        self.left = SHOT_RANGE

    def update(self, dt, game):
        step = min(self.left, SHOT_SPEED * dt)
        if step <= 0:
            return self.left > 0
        end_x, end_y = self.x + self.ux * step, self.y + self.uy * step
        walls = near_blocks(min(self.x, end_x) - self.radius, min(self.y, end_y) - self.radius,
                            max(self.x, end_x) + self.radius, max(self.y, end_y) + self.radius)
        wall = min((ray_rect_entry(self.x, self.y, self.ux, self.uy,
                    (l - self.radius, b - self.radius, r + self.radius, t + self.radius))
                    for l, b, r, t in walls), default=float('inf'))
        hero = game.hero
        hit = float('inf') if hero.dead else ray_circle_entry(
            self.x, self.y, self.ux, self.uy, hero.x, hero.y, 12 + self.radius)
        travel = min(step, wall, hit)
        self.x += self.ux * travel
        self.y += self.uy * travel
        self.left -= travel
        if wall <= min(step, hit):
            return False
        if hit <= step:
            if not hero.invulnerable and not game.dev.god:
                game.spit_hit(self)
            return False          # dodging consumes the shot; no delayed hit
        return self.left > 0

    def draw(self, cx, cy):
        # Effect only: body art is never drawn in code.
        x, y = self.x - cx, self.y - cy + 40
        q = 1 / DOT
        for ox, oy, r, colour in ((-self.ux * 5, -self.uy * 5, 1, (78, 112, 29)),
                                  (0, 0, 2, (117, 165, 31)), (0, 0, 1, (216, 246, 89))):
            px, py = round((x + ox) * DOT) / DOT, round((y + oy) * DOT) / DOT
            pico2d.draw_rectangle(px - r*q, py - r*q, px + r*q, py + r*q, *colour, filled=True)


class SpitterLook:
    def __init__(self, folder=ART):
        names = ('idle', 'walk_a', 'walk_b', 'windup', 'release', 'recover', 'hurt', 'down')
        self.images = {key: pico2d.load_image(str(Path(folder) / f'{key}.png'))
                       for name in names for key in (name, name + '_glow')}

    def draw_pose(self, name, x, y, facing, glow=0.):
        k = 32 / 54
        flip = '' if facing > 0 else 'h'
        for key, alpha in ((name, 1.), (name + '_glow', glow)):
            if alpha <= 0:
                continue
            im = self.images[key]
            im.opacify(alpha)
            try:
                im.composite_draw(0, flip, x, y + (58 - 32) / k, 64/k, 64/k)
            finally:
                im.opacify(1.)


class Spitter(Zombie):
    ranged = True

    def __init__(self, look, x, y):
        super().__init__(look, x, y, crawler=False)
        self.pace = .65
        self.aim = (x + 1, y)

    @property
    def reach(self):
        return ATTACK_RANGE

    @property
    def speed(self):
        return 46.0  # no discovery sprint for this heavy mutant

    def hurt(self, from_x, from_y, damage=1, part='torso', push=55, stagger=False):
        # Prototype has no crawler sheet; leg hits interrupt instead of making a fake crawl.
        return super().hurt(from_x, from_y, damage, 'torso' if part == 'legs' else part, push, stagger)

    def update(self, dt, hero, game):
        if self.state in ('windup', 'strike', 'recover'):
            self.time += dt
            self.spotted = max(0., self.spotted - dt)
            self.flash = max(0., getattr(self, 'flash', 0.) - dt)
            self.timer -= dt
            if self.timer <= 0:
                if self.state == 'windup':
                    if not hero.dead:
                        game.projectiles.append(SpitShot(self, self.aim))
                    self.state, self.timer = 'strike', RELEASE
                elif self.state == 'strike':
                    self.state, self.timer = 'recover', RECOVER
                else:
                    self.state = 'chase'
            return None
        old = self.state
        super().update(dt, hero, game)
        if self.state == 'windup' and old != 'windup':
            if hero is game.hero and not game.hero_sees(self):
                self.state = 'poised'  # don't launch the prototype from outside the player's view
            else:
                self.windup = self.timer = WINDUP
                self.aim = (hero.x, hero.y)  # locked now, never homes or tracks during the tell
                self.heading = atan2(hero.y - self.y, hero.x - self.x)
                self.facing = 1 if cos(self.heading) >= 0 else -1
        return None

    def draw_body(self, cx, cy):
        glow = 0.
        pose = 'idle'
        if self.state == 'dead':
            pose = 'down'
        elif self.state == 'windup':
            pose, glow = 'windup', .25 + .75 * max(0., 1 - self.timer / WINDUP)
        elif self.state == 'strike':
            pose, glow = 'release', 1.
        elif self.state == 'recover':
            pose = 'recover'
        elif self.state in ('flinch', 'stagger'):
            pose = 'hurt'
        elif self.state in ('chase', 'search'):
            pose = 'walk_a' if int(self.walk * 2) % 2 == 0 else 'walk_b'
        self.look.draw_pose(pose, self.x - cx, self.y - cy, self.facing, glow)
        if self.spotted > 0 and self.alive and self.show_marks:
            ui.world_text_center(self.x - cx, self.y - cy + 72, '!', (255, 220, 90), 22)
