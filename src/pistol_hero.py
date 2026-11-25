"""Red-jacket hero in the default game (2026-11-25, docs/plans/2026-11-25_권총주인공_기본연결.md).

Gun in hand -> the D pistol look (8 contact walk keys, FACE-R1 shared head, moving shot keeps the
legs walking). A melee weapon in hand -> the red-jacket melee look (6 walk keys, 3 cut keys).
Q / the bag swaps weapons as before; the drawing follows the weapon in hand.
Ported from tools/pistol_flow_look.py, pistol_gait_look.py, run_pistol_comparison.py (D, refined)
and run_redjacket_trial.py, so the game does not import tools/. Only left/right art exists:
up/down are the side view, backwards replays the walk, a roll shows `settle` + the old afterimages.
BUSAN_HERO=sword keeps the old 3D sword hero.
"""
import json
from math import atan2, cos, hypot, sin

import pico2d

import weapons
from play import Game
from settings import DOT, ROOT

PREV = ROOT / "assets/characters/previews"
FLOW = PREV / "hero_pistol_flow_v3"        # fall/down art and the base muzzle points
GAIT = PREV / "hero_pistol_gait_v4"        # D: stride lengths and walk muzzles
IDENTITY = GAIT / "identity"               # FACE-R1: one head drawing shared by all of these
MELEE = PREV / "hero_redjacket_motion_v1"
K = 32 / 54                                # art px -> world, as in the trials


def _blit(im, x, feet_y, facing, alpha):
    im.opacify(alpha)
    try:
        im.composite_draw(0, "" if facing > 0 else "h", x, feet_y + 26 / K, 64 / K, 64 / K)
    finally:
        im.opacify(1.)


class PistolLook:
    """D refined (the F10 '수정 후' path of the comparison trial)."""
    FRAME_TIME = .12
    WALK_KEYS = 8
    keys = {}

    def __init__(self, base):
        self.base = base
        self.images = {name: pico2d.load_image(str(FLOW / f"{name}.png")) for name in ("fall", "down")}
        self.sources = {}
        for name in ("low", "raise", "aim", "recoil", "settle", "hurt"):
            self._load(name, IDENTITY / f"{name}.png")
        for gait in ("walk", "aim_walk"):
            for i in range(8):
                folder = IDENTITY / "refinement" if i in (2, 6) else IDENTITY
                self._load(f"{gait}_{i}", folder / f"{gait}_{i}.png")
        self.muzzles = json.loads((FLOW / "muzzles.json").read_text(encoding="utf-8"))["points"]
        self.muzzles.update(json.loads((GAIT / "muzzles.json").read_text(encoding="utf-8"))["points"])
        self.STRIDES = json.loads((GAIT / "gait_meta.json").read_text(encoding="utf-8"))["cycle_distance_world"]
        self.reset()

    def _load(self, key, path):
        self.images[key] = pico2d.load_image(str(path))
        self.sources[key] = path

    def __getattr__(self, name):
        return getattr(self.base, name)

    def has(self, pose):
        return pose.startswith("ready_") or pose in ("idle", "walk", "run", "sneak")

    def has_dir(self, pose, angle):
        return False

    def blade_lines(self, *args, **kwargs):
        return None

    def reset(self):
        self.phase = 0.; self.raise_amount = 0.; self.settling = 0.; self.recoil = 0.; self.linger = 0.
        self.was_moving = False; self.seen_shot = None; self.sprite = "low"; self.contacts = []
        self.last_state = ("D", "low")

    def advance(self, hero, dt, dx=0., dy=0.):
        self.contacts = []
        if dt <= 0:
            return
        old = self.phase
        self.recoil = max(0., self.recoil - dt); self.linger = max(0., self.linger - dt)
        self.settling = max(0., self.settling - dt)
        shot = hero.slash if hero.slash and hero.slash["weapon"].get("shot") else None
        if shot is not None and shot.get("hit") and shot is not self.seen_shot:
            self.seen_shot = shot; self.recoil = .11; self.linger = .18
        aimed = hero.ready is not None or shot is not None or self.linger > 0
        self.raise_amount = max(0., min(1., self.raise_amount + (1 if aimed else -1) * dt / .12))
        moving = hero.moving and hero.roll <= 0 and hypot(dx, dy) > 1e-6
        if moving:
            stride = self.STRIDES["aim_walk" if aimed else "walk"]
            direction = -1 if dx * hero.facing < -.01 else 1
            self.phase = (self.phase + direction * hypot(dx, dy) / stride) % 1
        if self.was_moving and not moving and aimed:
            self.settling = .09
        self.was_moving = moving
        if hero.dead:
            self.sprite = "fall" if hero.dead < .22 else "down"
        elif hero.reeling > 0:
            self.sprite = "hurt"
        elif hero.roll > 0:
            self.sprite = "settle"
        elif moving:
            gait = "aim_walk" if aimed else "walk"
            self.sprite = f"{gait}_{int(self.phase * self.WALK_KEYS) % self.WALK_KEYS}"
        elif self.recoil > 0:
            self.sprite = "recoil"
        elif self.settling > 0:
            self.sprite = "settle"
        elif .12 < self.raise_amount < .88:
            self.sprite = "raise"
        else:
            self.sprite = "aim" if self.raise_amount >= .88 else "low"
        self.last_state = ("D", self.sprite)
        if self.sprite.startswith(("walk_", "aim_walk_")):
            before, after = int(old * 2), int(self.phase * 2)
            if before != after:        # a foot-contact boundary: event timing, not foot IK
                backwards = dx * hero.facing < -.01
                key = (4 if before == 1 else 0) if backwards else (4 if after == 1 else 0)
                self.contacts = [{"key": key, "x": hero.x + 4 / DOT * hero.facing, "y": hero.y + 1 / DOT}]

    def muzzle(self, hero, key):
        px, py = self.muzzles.get(key, self.muzzles["aim"])
        return hero.x + (px - 32) / K * hero.facing, hero.y + (58 - py) / K

    def firing_muzzle(self, hero):
        key = f"aim_walk_{int(self.phase * self.WALK_KEYS) % self.WALK_KEYS}" if hero.moving else "recoil"
        return self.muzzle(hero, key)

    def draw(self, pose, time, x, feet_y, facing, contact=None, distance=None, alpha=1., held=None,
             tint=None, angle=None, **kwargs):
        _blit(self.images[self.sprite], x, feet_y, facing, alpha)
        return None


class MeleeLook:
    """Red jacket with a blade: distance-driven walk and a contact-timed three-key cut."""
    FRAME_TIME = .13
    keys = {}

    def __init__(self, base):
        self.base = base
        names = ("idle", "guard", "windup", "impact", "recover") + tuple(f"walk_{i}" for i in range(6))
        self.images = {name: pico2d.load_image(str(MELEE / f"{name}.png")) for name in names}
        self.travel = 0.
        self.last_state = ("melee", "idle")

    def __getattr__(self, name):
        return getattr(self.base, name)

    def has(self, pose):
        return pose.startswith("ready_") or pose in ("idle", "run", "walk")

    def has_dir(self, pose, angle):
        return False

    def blade_lines(self, *args, **kwargs):
        return None

    def reset(self):
        self.travel = 0.

    def frame(self, pose, time, contact=None):
        if pose in ("walk", "run", "sneak") or (pose.startswith("ready_") and not pose.startswith("ready_stand_")):
            return f"walk_{int(self.travel / 64 * 6) % 6}"
        if pose in ("chop", "swing", "swingh", "stab"):
            hit = .48 if contact is None else contact
            if time < hit:
                return "windup"
            return "impact" if (time - hit) / max(1e-6, 1 - hit) < .38 else "recover"
        if pose.startswith("ready_stand_"):
            return "windup"
        return "guard" if pose == "push" else "idle"

    def draw(self, pose, time, x, feet_y, facing, contact=None, distance=None, alpha=1., held=None,
             tint=None, angle=None, **kwargs):
        key = self.frame(pose, time, contact)
        self.last_state = ("melee", key)
        _blit(self.images[key], x, feet_y, facing, alpha)
        return None


def gun_in_hand(hero):
    return bool(hero.weapon.get("shot"))


class RedJacketGame(Game):
    """The default game with the red-jacket hero: pistol in hand, the machete in the bag."""

    def __init__(self):
        super().__init__()
        self.pistol_look = PistolLook(self.hero_look)
        self.melee_look = MeleeLook(self.hero_look)
        self.foot_contacts = 0
        self.reset()

    def reset(self):
        super().reset()
        if not hasattr(self, "pistol_look"):
            return                                   # Game.__init__'s own reset, looks not loaded yet
        hero = self.hero
        hero.weapon = weapons.WEAPONS["pistol"]
        self.ammo = hero.weapon["shot"]["rounds"]    # the normal pistol rule: it comes loaded
        self.bag[weapons.item(weapons.DEFAULT)] = self.bag.get(weapons.item(weapons.DEFAULT), 0) + 1
        hero.walk_while_shooting = True
        hero.distance_step_audio = False             # D plays its own contact steps
        self.pistol_look.reset(); self.melee_look.reset()
        self._wear()

    def _wear(self):
        hero = self.hero
        gun = gun_in_hand(hero)
        hero.look = self.pistol_look if gun else self.melee_look
        hero.walk_while_shooting = gun
        hero.distance_step_audio = not gun

    def update(self, dt, keys):
        hero = self.hero
        self._wear()
        x, y, t = hero.x, hero.y, hero.time
        super().update(dt, keys)
        if self.hero is not hero:
            self._wear()
            return
        self._wear()
        if gun_in_hand(hero):
            if self.aim[0] is not None and (hero.ready is not None or hero.slash):
                ax, _ = self.mouse_world(*self.aim)
                hero.facing = 1 if ax >= hero.x else -1
            self.pistol_look.advance(hero, max(0., hero.time - t), hero.x - x, hero.y - y)
            from dodge_fx import Dust
            for contact in self.pistol_look.contacts:
                self.foot_contacts += 1
                self.sounds.play("step", .08 if hero.sneaking else .20)
                if not hero.sneaking:
                    self.effects.append(Dust(contact["x"], contact["y"], atan2(hero.y - y, hero.x - x), kind="step"))
        elif hero.moving:
            self.melee_look.travel += hypot(hero.x - x, hero.y - y)

    def fire(self, slash, shot):
        """Same damage/ammo/noise rules as Game.fire, but the bullet leaves the drawn muzzle."""
        import area
        from settings import CHEST
        from slash_fx import Spark, Tracer
        from vision_cone import ray_hit
        hero = self.hero
        self.ammo -= 1
        if self.aim[0] is not None:
            ax, _ = self.mouse_world(*self.aim)
            hero.facing = 1 if ax >= hero.x else -1
        ox, oy = self.pistol_look.firing_muzzle(hero)
        angle = slash["angle"]
        if self.aim[0] is not None:
            ax, ay = self.mouse_world(*self.aim)
            angle = atan2(ay - oy, ax - ox)
        ux, uy = cos(angle), sin(angle)
        reach = shot["range"]
        limit = min(reach, ray_hit(ox, oy, ux, uy, area.sight_blocks(ox - reach, oy - reach, ox + reach, oy + reach)))
        struck, at = None, limit
        for z in self.zombies:
            if not z.alive:
                continue
            for up in ((6,) if z.prone else (8, CHEST, 40)):
                dx, dy = z.x - ox, z.y + up - oy
                t = dx * ux + dy * uy
                if 0 < t < at and abs(dx * uy - dy * ux) <= shot["width"]:
                    struck, at = z, t
        self.effects.append(Tracer(ox, oy, ox + ux * at, oy + uy * at))
        self.effects.append(Spark(ox, oy))
        self.sounds.play("shot", 1.)
        self.jolt("light")
        if self.senses:
            self.make_noise(shot["noise"])
        return struck

    def draw_aim(self, cx, cy):
        hero = self.hero
        flow = self.pistol_look
        if not gun_in_hand(hero):
            return super().draw_aim(cx, cy)
        if self.aim[0] is None or hero.dead or self.left or self.bag_open or hero.slash or flow.raise_amount < .88:
            return
        import area
        import ui
        from vision_cone import ray_hit
        sx, sy = flow.muzzle(hero, flow.sprite)
        tx, ty = self.mouse_world(*self.aim)
        ang = atan2(ty - sy, tx - sx)
        ux, uy = cos(ang), sin(ang)
        length = hero.weapon["shot"]["range"]
        far = min(length, ray_hit(sx, sy, ux, uy, area.sight_blocks(sx - length, sy - length, sx + length, sy + length)))
        colour = (196, 170, 92) if hero.charge >= 1 else (176, 172, 158) if self.ammo else (120, 60, 54)
        for distance in range(8, int(far), 3 * self.DOT_GAP):
            x = round((sx + ux * distance - cx) * DOT) / DOT
            y = round((sy + uy * distance - cy) * DOT) / DOT
            pico2d.draw_rectangle(x, y, x + 1.99 / DOT, y + 1.99 / DOT, *colour, filled=True)
        target = self.aimed(*self.aim) if hero.charge >= 1 else None
        if target is not None:
            z, part = target
            low, high, half = (0, 14, weapons.PART_HALF_WIDTH * 2) if z.prone else next(
                (lo, hi, weapons.PART_HALF_WIDTH) for p, lo, hi in weapons.PARTS if p == part)
            left, right = z.x - half - cx, z.x + half - cx
            bottom, top = z.y + low - cy, z.y + min(high, 56) - cy
            for x0, y0, dx, dy in ((left, top, 1, -1), (right, top, -1, -1), (left, bottom, 1, 1), (right, bottom, -1, 1)):
                pico2d.draw_rectangle(min(x0, x0 + 5 * dx), y0 - 1, max(x0, x0 + 5 * dx), y0, *colour, filled=True)
                pico2d.draw_rectangle(x0, min(y0, y0 + 5 * dy), x0 + 1, max(y0, y0 + 5 * dy), *colour, filled=True)
            ui.world_text_center(z.x - cx, z.y + (24 if z.prone else 62) - cy, weapons.PART_NAMES[part], colour, 12)
