"""Top-down combat prototype (탑뷰 시험판), to compare with src/proto_side.py.

Same rules as the side-scroll prototype, only the view changes:
- WASD moves freely on the ground (no gravity, no jump); wrecked cars block the way
- left click: one instant slash towards the mouse, a short lunge, a big crescent; one hit kills
- infected come from every side, show "!" and strike; the hero takes 2 hits
- Space: roll (invulnerable); right button held: time crawls, exposure rises
- dying restarts the room at once (R also restarts)
- facing vision (2026-11-14): only the cone toward the mouse and a small circle around the
  hero are lit, wrecks cast shadows; infected in the dark are not drawn (vision_cone.py)
- infected senses (2026-11-14, from Project Zomboid's public rules, docs/planning/
  ZOMBOID_VISUAL_REFERENCE.md): they find the hero by sight (a cone ahead of them, blocked by
  wrecks) or by sound (steps, rolls, slashes), go to the last place they saw or heard him and
  forget after a while; a blow from outside the hero's own sight gives a shorter warning.
  F2 switches back to the old rule (chase anything within 300 px) to compare.
- from Zomboid's own state files (docs/research/ZOMBOID_REA_ANALYSIS.md): an infected strikes
  only once it has seen the hero for 0.5 s (before that it hangs back, poised); on a noise it
  first turns toward it (0.3-0.6 s, each one differently) before setting off; when a blow lands
  while another infected is also on the hero, they grab him: no moving or slashing for a moment,
  only a roll breaks free.

Characters reuse the side-view sheets (seen from a 3/4 angle), so this is only a feel test.

    .venv\\Scripts\\python.exe src\\proto_top.py
"""

import random
import sys
from math import atan2, cos, hypot, pi, sin
from pathlib import Path

import pico2d
import sdl2
from pico2d import pico2d as canvas

sys.path.insert(0, str(Path(__file__).parent))

import ui  # noqa: E402
from character_look import SheetLook  # noqa: E402
from vision_cone import CONE_HALF, VisionCone, ray_hit  # noqa: E402
from proto_side import (EXPOSURE_FALL, EXPOSURE_RISE, HEIGHT, HERO_HP, HURT_INVULNERABLE,  # noqa: E402
                        ROLL_COOLDOWN, ROLL_SPEED, ROLL_TIME, ROOT, SCALE, SLASH_ARC, SLASH_COOLDOWN,
                        SLASH_HIT, SLASH_LUNGE, SLASH_REACH, SLASH_TIME, SLOW_WORLD, VIEW_H, VIEW_W, WIDTH,
                        ZOMBIE_RECOVER, ZOMBIE_REACH, ZOMBIE_SPEED, ZOMBIE_STRIKE, ZOMBIE_WINDUP, Crescent,
                        Spark)

ROOM_W, ROOM_H = 1000, 640
RUN_SPEED = 150.0
CHEST = 22                       # chest height above the feet, where blows land
# wrecked cars and rubble: (left, bottom, right, top) on the ground plane
BLOCKS = [(260, 300, 360, 340), (520, 120, 600, 160), (640, 420, 740, 460), (150, 500, 210, 560)]
# Infected senses (numbers are ours; the rules come from Zomboid's sight / hearing / memory).
SIGHT_RANGE = 260               # px an infected sees ahead of it
SIGHT_HALF = 1.1                # radians either side of where it faces
NOTICE_NEAR = 36                # px: so close it notices whatever way it faces
NOISE_STEP = 70                 # px the hero's footsteps carry
NOISE_ROLL = 140
NOISE_SLASH = 230
MEMORY = 3.0                    # s it keeps going to the last place it saw or heard the hero
WANDER_TURN = (2.0, 5.0)        # s between idle head turns
BLIND_WINDUP = 0.25             # s of warning when it strikes from outside the hero's sight
SEEN_BEFORE_STRIKE = 0.5        # s it must have seen the hero before it strikes (Zomboid: 0.5)
ALERT_TURN = (0.3, 0.6)         # s it spends turning toward a noise before going
GRAB_TIME = 0.9                 # s the hero is held when a blow lands with another one on him
GRAB_NEAR = ZOMBIE_REACH + 12   # px: "on the hero"
ZOMBIE_STARTS = [(520, 380), (820, 200), (860, 540), (380, 560), (700, 80)]


def blocked(x, y, pad=8):
    return (not (pad <= x <= ROOM_W - pad and pad <= y <= ROOM_H - pad)
            or any(l - pad <= x <= r + pad and b - pad / 2 <= y <= t + pad / 2 for l, b, r, t in BLOCKS))


def move_body(body, dx, dy):
    """Slide along obstacles one axis at a time."""
    if not blocked(body.x + dx, body.y):
        body.x += dx
    if not blocked(body.x, body.y + dy):
        body.y += dy


class Hero:
    def __init__(self, look):
        self.look = look
        self.x, self.y = 100.0, 300.0
        self.facing = 1
        self.hp = HERO_HP
        self.hurt = 0.0
        self.slash = None
        self.slash_cooldown = 0.0
        self.roll = 0.0
        self.roll_dir = (1.0, 0.0)
        self.roll_cooldown = 0.0
        self.lunge = (0.0, 0.0)
        self.run_distance = 0.0
        self.time = 0.0
        self.dead = 0.0
        self.moving = False
        self.grabbed = 0.0           # held by two or more infected (only a roll breaks free)

    @property
    def invulnerable(self):
        return self.roll > 0 or self.hurt > 0

    def start_slash(self, ax, ay):
        if self.slash or self.roll > 0 or self.slash_cooldown > 0 or self.dead or self.grabbed > 0:
            return
        angle = atan2(ay - (self.y + CHEST), ax - self.x)
        self.facing = 1 if cos(angle) >= 0 else -1
        self.slash = {"time": 0.0, "angle": angle, "hit": False}
        speed = SLASH_LUNGE / SLASH_HIT * 0.5
        self.lunge = (cos(angle) * speed, sin(angle) * speed)

    def start_roll(self, mx, my):
        if self.roll > 0 or self.roll_cooldown > 0 or self.dead:
            return
        length = hypot(mx, my)
        self.roll_dir = (mx / length, my / length) if length else (float(self.facing), 0.0)
        self.roll = ROLL_TIME
        self.slash = None
        self.grabbed = 0.0           # rolling tears free

    def update(self, dt, keys, aim_x):
        self.time += dt
        self.hurt = max(0.0, self.hurt - dt)
        self.slash_cooldown = max(0.0, self.slash_cooldown - dt)
        self.roll_cooldown = max(0.0, self.roll_cooldown - dt)
        if self.dead:
            self.dead += dt
            return
        mx = keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A]
        my = keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S]
        self.moving = False
        if self.grabbed > 0:
            self.grabbed -= dt
            return
        if self.roll > 0:
            self.roll -= dt
            move_body(self, self.roll_dir[0] * ROLL_SPEED * dt, self.roll_dir[1] * ROLL_SPEED * dt)
            if self.roll <= 0:
                self.roll_cooldown = ROLL_COOLDOWN
        elif self.slash:
            self.slash["time"] += dt
            move_body(self, self.lunge[0] * dt, self.lunge[1] * dt)
            self.lunge = (self.lunge[0] * 0.82, self.lunge[1] * 0.82)
            if self.slash["time"] >= SLASH_TIME:
                self.slash = None
                self.slash_cooldown = SLASH_COOLDOWN
        elif mx or my:
            length = hypot(mx, my)
            move_body(self, mx / length * RUN_SPEED * dt, my / length * RUN_SPEED * dt)
            self.run_distance += RUN_SPEED * dt / 32
            self.moving = True
            if mx:
                self.facing = mx
        elif aim_x is not None:
            self.facing = 1 if aim_x >= self.x else -1

    def draw(self, cx, cy):
        x, y = self.x - cx, self.y - cy
        if self.dead:
            self.look.draw("down", min(1.0, self.dead * 1.5), x, y, self.facing)
        elif self.hurt > 0 and int(self.hurt * 20) % 2 == 0:
            return
        elif self.roll > 0:
            face = 1 if self.roll_dir[0] >= 0 else -1
            self.look.draw("run", (1 - self.roll / ROLL_TIME) * 0.5, x, y - 2, face,
                           distance=self.run_distance + (1 - self.roll / ROLL_TIME) * 3)
        elif self.slash:
            self.look.draw("swing", self.slash["time"] / SLASH_TIME, x, y, self.facing,
                           contact=SLASH_HIT / SLASH_TIME)
        elif self.moving:
            self.look.draw("run", self.time, x, y, self.facing, distance=self.run_distance)
        else:
            self.look.draw("idle", self.time, x, y, self.facing)


class Zombie:
    def __init__(self, look, x, y):
        self.look = look
        self.x, self.y = float(x), float(y)
        self.facing = -1
        self.heading = random.uniform(-pi, pi)     # where it looks (its own sight cone)
        self.turn_in = random.uniform(*WANDER_TURN)
        self.state = "idle"          # idle, search (going to a seen/heard spot), chase, windup...
        self.target = None           # last place it saw or heard the hero
        self.memory = 0.0
        self.timer = 0.0
        self.windup = ZOMBIE_WINDUP
        self.seen_time = 0.0         # how long it has kept the hero in sight
        self.turn_from = self.turn_to = 0.0
        self.time = random.random()
        self.walk = 0.0
        self.death = (0.0, 0.0)

    @property
    def alive(self):
        return self.state != "dead"

    def kill(self, dx, dy):
        self.state, self.timer = "dead", 0.0
        length = hypot(dx, dy) or 1
        self.death = (dx / length * 160, dy / length * 160)

    def sees(self, hero):
        dx, dy = hero.x - self.x, hero.y - self.y
        dist = hypot(dx, dy)
        if hero.dead or dist > SIGHT_RANGE:
            return False
        if dist > NOTICE_NEAR:
            off = abs((atan2(dy, dx) - self.heading + pi) % (2 * pi) - pi)
            if off > SIGHT_HALF:
                return False
        return dist < 1 or ray_hit(self.x, self.y, dx / dist, dy / dist, BLOCKS) >= dist

    def hear(self, x, y, radius):
        if hypot(x - self.x, y - self.y) > radius:
            return
        if self.state == "idle":
            # Zomboid's alerted turn: first look toward the noise, then go.
            self.state, self.timer = "alert", random.uniform(*ALERT_TURN)
            self.turn_from, self.turn_to = self.heading, atan2(y - self.y, x - self.x)
            self.target, self.memory = (x, y), MEMORY
        elif self.state in ("search", "alert"):
            self.target, self.memory = (x, y), MEMORY

    def walk_to(self, x, y, dt):
        dx, dy = x - self.x, y - self.y
        dist = hypot(dx, dy)
        if dist < 1:
            return dist
        self.heading = atan2(dy, dx)
        if abs(dx) > 1:
            self.facing = 1 if dx > 0 else -1
        step = min(dist, ZOMBIE_SPEED * dt)
        move_body(self, dx / dist * step, dy / dist * step)
        self.walk += step / 32
        return dist

    def update(self, dt, hero, game):
        self.time += dt
        if self.state == "dead":
            self.timer += dt
            move_body(self, self.death[0] * dt, self.death[1] * dt)
            self.death = (self.death[0] * 0.9, self.death[1] * 0.9)
            return None
        dx, dy = hero.x - self.x, hero.y - self.y
        dist = hypot(dx, dy)
        event = None
        if not game.senses:
            if self.state in ("idle", "search") and dist < 300:          # the old rule
                self.state = "chase"
        elif self.state in ("idle", "alert", "search", "chase", "poised"):
            if self.sees(hero):
                self.seen_time += dt
                if self.state != "poised":
                    self.state = "chase"
                self.target, self.memory = (hero.x, hero.y), MEMORY
            else:
                self.seen_time = 0.0
                if self.state in ("chase", "poised"):
                    self.state = "search"                                # lost sight: go where it was
        if self.state == "idle":
            self.turn_in -= dt
            if self.turn_in <= 0:                                        # look around now and then
                self.heading += random.uniform(-1.6, 1.6)
                self.facing = 1 if cos(self.heading) >= 0 else -1
                self.turn_in = random.uniform(*WANDER_TURN)
        elif self.state == "alert":
            self.timer -= dt
            turn = (self.turn_to - self.turn_from + pi) % (2 * pi) - pi
            self.heading = self.turn_from + turn * max(0.0, 1 - self.timer / ALERT_TURN[1])
            self.facing = 1 if cos(self.heading) >= 0 else -1
            if self.timer <= 0:
                self.heading, self.state = self.turn_to, "search"
        elif self.state == "search":
            self.memory -= dt
            if self.walk_to(*self.target, dt) < 6 or self.memory <= 0:
                self.state, self.turn_in = "idle", 0.6                   # nothing here: give up
        elif self.state in ("chase", "poised"):
            if dist <= ZOMBIE_REACH and game.senses and self.seen_time < SEEN_BEFORE_STRIKE:
                self.state = "poised"            # just spotted: hang back, poised (Zomboid 0.5 s)
                self.heading = atan2(dy, dx)
                self.facing = 1 if dx > 0 else -1
            elif dist <= ZOMBIE_REACH:
                # From outside the hero's sight the warning is short (Zomboid: from the side
                # and behind they are far more dangerous).
                blind = game.senses and not game.hero_sees(self)
                self.windup = BLIND_WINDUP if blind else ZOMBIE_WINDUP
                self.state, self.timer = "windup", self.windup
                self.heading = atan2(dy, dx)
            else:
                self.state = "chase"
                self.walk_to(hero.x, hero.y, dt)
        elif self.state in ("windup", "strike", "recover"):
            self.timer -= dt
            if self.timer <= 0:
                if self.state == "windup":
                    self.state, self.timer = "strike", ZOMBIE_STRIKE
                    if dist <= ZOMBIE_REACH + 8:
                        event = "hit"
                elif self.state == "strike":
                    self.state, self.timer = "recover", ZOMBIE_RECOVER
                else:
                    self.state = "chase"
        return event

    def draw(self, cx, cy):
        x, y = self.x - cx, self.y - cy
        if self.state == "dead":
            if self.timer < 1.2 or int(self.timer * 12) % 2 == 0:
                self.look.draw("down", min(1.0, self.timer * 2), x, y, 1 if self.death[0] < 0 else -1)
        elif self.state == "windup":
            self.look.draw("attack", 0.25 * (1 - self.timer / self.windup), x, y, self.facing)
            ui.text_center(x, y + 66, "!", (255, 120, 80), 22)
        elif self.state == "strike":
            self.look.draw("attack", 0.45, x, y, self.facing)
        elif self.state == "recover":
            self.look.draw("attack", 0.5 + 0.5 * (1 - self.timer / ZOMBIE_RECOVER), x, y, self.facing)
        elif self.state == "poised":
            self.look.draw("attack", 0.08, x, y, self.facing)        # arms up, not yet striking
        elif self.state in ("chase", "search"):
            self.look.draw("walk", self.time, x, y, self.facing, distance=self.walk)
            if self.state == "search":
                ui.text_center(x, y + 66, "?", (220, 200, 120), 18)
        else:
            self.look.draw("idle", self.time, x, y, self.facing)


class Game:
    def __init__(self):
        self.hero_look = SheetLook(ROOT / "assets/characters/hero")
        self.zombie_look = SheetLook(ROOT / "assets/characters/infected")
        self.aim = (None, None)
        self.deaths = 0
        self.vision = VisionCone(BLOCKS)    # wrecks block the light
        self.senses = True                  # F2: infected senses on/off (compare)
        self.look = 0.0
        random.seed(4)
        self.cracks = [(random.uniform(0, ROOM_W), random.uniform(0, ROOM_H), random.uniform(-1, 1))
                       for _ in range(70)]
        self.reset()

    def reset(self):
        self.hero = Hero(self.hero_look)
        self.zombies = [Zombie(self.zombie_look, x, y) for x, y in ZOMBIE_STARTS]
        self.effects = []
        self.cam = [0.0, 0.0]
        self.hitstop = self.shake = 0.0
        self.slow = False
        self.slow_blend = 0.0
        self.exposure = 0.0
        self.message = "WASD 이동 · 좌클릭 베기 · Space 구르기 · 우클릭 시간 느리게 · R 다시 · F2 감각 비교"
        self.cleared = False

    def mouse_world(self, sx, sy):
        return sx / SCALE + self.cam[0], (HEIGHT - 1 - sy) / SCALE + self.cam[1]

    def click(self, sx, sy):
        self.aim = (sx, sy)
        self.hero.start_slash(*self.mouse_world(sx, sy))

    def key_down(self, key, keys):
        if key == sdl2.SDLK_SPACE:
            self.hero.start_roll(keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A],
                                 keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S])
        elif key == sdl2.SDLK_r:
            self.reset()
        elif key == sdl2.SDLK_F2:
            self.senses = not self.senses
            self.reset()
            self.message = ("피폭체 감각 켬: 보고 듣고 찾음, 시야 밖 공격은 예고가 짧음" if self.senses
                            else "피폭체 감각 끔: 예전 규칙(300px 안이면 무조건 쫓아옴)")

    def hero_sees(self, zombie):
        """Is the infected inside the hero's view cone? (The small lit circle around the body
        does not count: what comes from the side or behind is still a blind-side attack.)"""
        off = abs((atan2(zombie.y - self.hero.y, zombie.x - self.hero.x) - self.look + pi) % (2 * pi) - pi)
        return off <= CONE_HALF

    def make_noise(self, radius):
        for z in self.zombies:
            if z.alive:
                z.hear(self.hero.x, self.hero.y, radius)

    def update(self, real_dt, keys):
        hero = self.hero
        self.slow_blend = max(0.0, min(1.0, self.slow_blend + (1 if self.slow and not hero.dead else -1)
                                       * real_dt / 0.12))
        if self.slow and not hero.dead:
            self.exposure = min(100.0, self.exposure + EXPOSURE_RISE * real_dt)
            if self.exposure >= 100:
                self.slow = False
                self.message = "피폭 한계! 시간이 돌아옵니다"
        else:
            self.exposure = max(0.0, self.exposure - EXPOSURE_FALL * real_dt)
        self.shake = max(0.0, self.shake - real_dt)
        if self.hitstop > 0:
            self.hitstop -= real_dt
            return
        world_dt = real_dt * (1 + (SLOW_WORLD - 1) * self.slow_blend)
        aim_x = self.mouse_world(*self.aim)[0] if self.aim[0] is not None else None
        hero.update(real_dt, keys, aim_x)
        if self.aim[0] is not None:          # the hero looks toward the mouse
            ax, ay = self.mouse_world(*self.aim)
            self.look = atan2(ay - (hero.y + CHEST), ax - hero.x)
        else:
            self.look = 0.0 if hero.facing > 0 else pi

        if hero.slash and not hero.slash["hit"] and hero.slash["time"] >= SLASH_HIT:
            hero.slash["hit"] = True
            sx, sy = hero.x, hero.y + CHEST
            self.effects.append(Crescent(sx, sy, hero.slash["angle"]))
            for z in self.zombies:
                if not z.alive:
                    continue
                zx, zy = z.x, z.y + CHEST
                diff = (atan2(zy - sy, zx - sx) - hero.slash["angle"] + pi) % (2 * pi) - pi
                if hypot(zx - sx, zy - sy) <= SLASH_REACH + 12 and abs(diff) <= SLASH_ARC:
                    z.kill(zx - sx, zy - sy)
                    self.effects.append(Spark(zx, zy + 4, big=True))
                    self.hitstop, self.shake = max(self.hitstop, 0.07), 0.12

        if self.senses and not hero.dead:          # the hero's noise: steps, rolls, slashes
            if hero.slash and hero.slash["time"] <= real_dt:
                self.make_noise(NOISE_SLASH)
            elif hero.roll > 0 and hero.roll >= ROLL_TIME - real_dt:
                self.make_noise(NOISE_ROLL)
            elif hero.moving:
                self.make_noise(NOISE_STEP)
        for z in self.zombies:
            if z.update(world_dt, hero, self) == "hit" and not hero.invulnerable and not hero.dead:
                hero.hp -= 1
                hero.hurt = HURT_INVULNERABLE
                others = sum(1 for o in self.zombies if o is not z and o.alive
                             and hypot(o.x - hero.x, o.y - hero.y) <= GRAB_NEAR)
                if self.senses and others and hero.hp > 0:
                    hero.grabbed = GRAB_TIME             # Zomboid's drag-down: two on him hold him
                    hero.slash = None
                    self.message = "붙잡혔다! Space로 구르면 빠져나감"
                self.effects.append(Spark(hero.x, hero.y + 26))
                self.hitstop, self.shake = 0.1, 0.2
                if hero.hp <= 0:
                    hero.dead = 0.001
                    self.deaths += 1
                    self.message = "쓰러졌다… 바로 다시 시작"
        self.effects = [e for e in self.effects if e.update(real_dt)]
        if hero.dead > 0.9:
            self.reset()
            return
        if not self.cleared and all(not z.alive for z in self.zombies):
            self.cleared = True
            self.message = "구역 정리! R로 다시 해 보기"
        for i, (pos, view, room) in enumerate(((hero.x, VIEW_W, ROOM_W), (hero.y, VIEW_H, ROOM_H))):
            target = max(0, min(room - view, pos - view / 2))
            self.cam[i] += (target - self.cam[i]) * min(1.0, real_dt * 8)

    def draw(self):
        if not hasattr(self, "target"):
            self.target = sdl2.SDL_CreateTexture(canvas.renderer, sdl2.SDL_PIXELFORMAT_RGBA8888,
                                                 sdl2.SDL_TEXTUREACCESS_TARGET, VIEW_W, VIEW_H)
            sdl2.SDL_SetTextureBlendMode(self.target, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetRenderTarget(canvas.renderer, self.target)
        sdl2.SDL_SetRenderDrawColor(canvas.renderer, 30, 30, 34, 255)
        sdl2.SDL_RenderClear(canvas.renderer)
        canvas.canvas_height = VIEW_H
        shake = random.uniform(-2, 2) if self.shake > 0 else 0
        cx, cy = self.cam[0] + shake, self.cam[1]
        # asphalt: lane lines and cracks
        for lane in range(80, ROOM_H, 160):
            for x0 in range(0, ROOM_W, 60):
                pico2d.draw_rectangle(x0 - cx, lane - cy, x0 + 30 - cx, lane + 2 - cy, 120, 110, 80, filled=True)
        for x, y, t in self.cracks:
            pico2d.draw_line(x - cx, y - cy, x + 14 - cx, y + 10 * t - cy, 20, 20, 24)
        pico2d.draw_rectangle(-cx, -cy, ROOM_W - cx, ROOM_H - cy, 70, 64, 60)
        # sort everything on the ground by depth: lower on screen = nearer = drawn later
        things = [(b[1], "block", b) for b in BLOCKS]
        things += [(z.y, "z", z) for z in self.zombies]
        things.append((self.hero.y, "hero", self.hero))
        eye = (self.hero.x, self.hero.y)                  # on the ground
        for _, kind, obj in sorted(things, key=lambda t: -t[0]):
            if kind == "z" and not self.vision.visible(eye, self.look, obj.x, obj.y):
                continue                                   # out of sight: not drawn at all
            if kind == "block":
                l, b, r, t = obj
                pico2d.draw_rectangle(l - cx, b - cy, r - cx, t + 18 - cy, 44, 38, 36, filled=True)
                pico2d.draw_rectangle(l - cx, t - cy, r - cx, t + 18 - cy, 70, 60, 54, filled=True)
                pico2d.draw_line(l - cx, t + 18 - cy, r - cx, t + 18 - cy, 140, 120, 96)
            else:
                obj.draw(cx, cy)
        for e in self.effects:
            _draw_effect(e, cx, cy)
        self.vision.draw((self.hero.x, self.hero.y), self.look, (self.hero.x - cx, self.hero.y + CHEST - cy),
                         VIEW_W, VIEW_H)
        if self.slow_blend > 0:
            pico2d.draw_rectangle(0, 0, VIEW_W, VIEW_H, 20, 60, 70, round(80 * self.slow_blend), filled=True)
        sdl2.SDL_SetRenderTarget(canvas.renderer, None)
        canvas.canvas_height = HEIGHT
        sdl2.SDL_RenderCopy(canvas.renderer, self.target, None, sdl2.SDL_Rect(0, 0, WIDTH, HEIGHT))
        pico2d.draw_rectangle(0, HEIGHT - 50, WIDTH, HEIGHT, 10, 12, 16, 200, filled=True)
        ui.text(12, HEIGHT - 20, "[탑뷰] " + self.message, ui.ACCENT, 14)
        ui.text(12, HEIGHT - 42, "체력", ui.PARTY, 14)
        for i in range(HERO_HP):                 # boxes drawn, the font has no square glyphs
            pico2d.draw_rectangle(52 + i * 18, HEIGHT - 48, 64 + i * 18, HEIGHT - 36, 230, 90, 80,
                                  filled=i < self.hero.hp)
        ui.text(150, HEIGHT - 42, f"피폭 {self.exposure:4.0f}%   쓰러진 횟수 {self.deaths}", (150, 230, 160), 14)


def _draw_effect(effect, cx, cy):
    """Side-scroll effects only shift by x; shift y as well for the top-down camera."""
    effect.y -= cy
    effect.draw(cx)
    effect.y += cy


def main(window_x=None):
    pico2d.open_canvas(WIDTH, HEIGHT, sync=True)
    if window_x is not None:
        sdl2.SDL_SetWindowPosition(canvas.window, window_x, 120)
    sdl2.SDL_SetWindowTitle(canvas.window, "탑뷰 시험판".encode("utf-8"))
    ui.enable_blending()
    game = Game()
    last = pico2d.get_time()
    running = True
    while running:
        now = pico2d.get_time()
        dt = min(0.05, now - last)
        last = now
        keys = sdl2.SDL_GetKeyboardState(None)
        for event in pico2d.get_events():
            if event.type == sdl2.SDL_QUIT or (event.type == sdl2.SDL_KEYDOWN and event.key == sdl2.SDLK_ESCAPE):
                running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                game.key_down(event.key, keys)
            elif event.type == sdl2.SDL_MOUSEMOTION:
                game.aim = (event.x, event.y)
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_LEFT:
                game.click(event.x, event.y)
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_RIGHT:
                game.slow = True
            elif event.type == sdl2.SDL_MOUSEBUTTONUP and event.button == sdl2.SDL_BUTTON_RIGHT:
                game.slow = False
        game.update(dt, keys)
        pico2d.clear_canvas()
        game.draw()
        pico2d.update_canvas()
    pico2d.close_canvas()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
