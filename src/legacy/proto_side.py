"""Side-scrolling combat prototype (시험판): Katana Zero-style rules on our art.

Run on its own (the main game is untouched):

    .venv\\Scripts\\python.exe src\\proto_side.py

Rules being tested (docs: NEW_DIRECTION 2026-11-13):
- pure side view: gravity, jump, platforms
- left click: one instant slash towards the mouse, a short lunge, a big crescent; one hit kills
- infected chase along the floor and platforms, show "!" and strike; the hero takes 2 hits
- Space: roll (invulnerable); right button held: time crawls, exposure rises
- dying restarts the room at once (R also restarts)
"""

import random
import sys
from math import atan2, cos, hypot, pi, sin
from pathlib import Path

import pico2d
import sdl2
from pico2d import pico2d as canvas

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # shared modules in src/

import ui  # noqa: E402
from character_look import SheetLook  # noqa: E402

WIDTH, HEIGHT = 768, 432        # window
SCALE = 1.5                     # the world is drawn zoomed in, so the pixels read chunky
VIEW_W, VIEW_H = round(WIDTH / SCALE), round(HEIGHT / SCALE)   # 512 x 288 world px on screen
ROOM_WIDTH = 1300
FLOOR = 40                      # y of the ground line
GRAVITY = 1300.0
RUN_SPEED = 150.0
JUMP_SPEED = 400.0
ROLL_SPEED = 260.0
ROLL_TIME = 0.28
ROLL_COOLDOWN = 0.35
SLASH_TIME = 0.26               # whole slash
SLASH_HIT = 0.06                # when the blade connects
SLASH_LUNGE = 46.0              # px travelled along the aim
SLASH_REACH = 58.0
SLASH_ARC = 1.25                # radians either side of the aim
SLASH_COOLDOWN = 0.08
HERO_HP = 2
HURT_INVULNERABLE = 0.8
SLOW_WORLD = 0.12
EXPOSURE_RISE = 16.0            # per real second while time crawls
EXPOSURE_FALL = 3.0
ZOMBIE_SPEED = 70.0
ZOMBIE_REACH = 30.0
ZOMBIE_WINDUP = 0.5
ZOMBIE_STRIKE = 0.15
ZOMBIE_RECOVER = 0.6

# Platforms: (left, right, top). The floor is FLOOR across the room.
PLATFORMS = [(300, 420, 105), (520, 640, 165), (780, 920, 105), (1060, 1180, 165)]
ZOMBIE_STARTS = [(470, FLOOR), (850, 105), (1150, FLOOR)]


def floor_under(x, y, top_margin=6):
    """Highest standing surface at or below y for a body at x."""
    best = FLOOR
    for left, right, top in PLATFORMS:
        if left <= x <= right and top <= y + top_margin and top > best:
            best = top
    return best


class Body:
    """Shared gravity and floor handling."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.on_ground = True

    def fall(self, dt, drop_through=False):
        self.vy -= GRAVITY * dt
        self.y += self.vy * dt
        ground = FLOOR if drop_through else floor_under(self.x, self.y - self.vy * dt)
        if self.y <= ground and self.vy <= 0:
            self.y = ground
            self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False
        self.x = max(20.0, min(ROOM_WIDTH - 20.0, self.x))


class Hero(Body):
    def __init__(self, look):
        super().__init__(120, FLOOR)
        self.look = look
        self.facing = 1
        self.hp = HERO_HP
        self.hurt = 0.0
        self.slash = None           # dict(time, angle, hit_done)
        self.slash_cooldown = 0.0
        self.roll = 0.0
        self.roll_dir = 1
        self.roll_cooldown = 0.0
        self.run_distance = 0.0
        self.time = 0.0
        self.dead = 0.0

    @property
    def invulnerable(self):
        return self.roll > 0 or self.hurt > 0

    def start_slash(self, aim_x, aim_y):
        if self.slash or self.roll > 0 or self.slash_cooldown > 0 or self.dead:
            return
        angle = atan2(aim_y - (self.y + 22), aim_x - self.x)
        self.facing = 1 if cos(angle) >= 0 else -1
        self.slash = {"time": 0.0, "angle": angle, "hit": False}
        # the lunge: along the aim, a little lift when aiming up
        self.vx = cos(angle) * SLASH_LUNGE / SLASH_HIT * 0.5
        if sin(angle) > 0.3:
            self.vy = max(self.vy, 260 * sin(angle))

    def start_roll(self, direction):
        if self.roll > 0 or self.roll_cooldown > 0 or self.dead:
            return
        self.roll = ROLL_TIME
        self.roll_dir = direction or self.facing
        self.slash = None

    def update(self, dt, keys, aim_x):
        self.time += dt
        self.hurt = max(0.0, self.hurt - dt)
        self.slash_cooldown = max(0.0, self.slash_cooldown - dt)
        self.roll_cooldown = max(0.0, self.roll_cooldown - dt)
        if self.dead:
            self.dead += dt
            self.fall(dt)
            return
        move = keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A]
        if self.roll > 0:
            self.roll -= dt
            self.x += self.roll_dir * ROLL_SPEED * dt
            if self.roll <= 0:
                self.roll_cooldown = ROLL_COOLDOWN
        elif self.slash:
            self.slash["time"] += dt
            self.x += self.vx * dt
            self.vx *= 0.82
            if self.slash["time"] >= SLASH_TIME:
                self.slash = None
                self.slash_cooldown = SLASH_COOLDOWN
                self.vx = 0.0
        else:
            self.x += move * RUN_SPEED * dt
            if move:
                self.facing = move
                self.run_distance += abs(move) * RUN_SPEED * dt / 32
            elif aim_x is not None:
                self.facing = 1 if aim_x >= self.x else -1
            if keys[sdl2.SDL_SCANCODE_W] and self.on_ground:
                self.vy = JUMP_SPEED
        drop = keys[sdl2.SDL_SCANCODE_S] and self.on_ground and self.y > FLOOR
        if drop:
            self.y -= 8
        self.fall(dt, drop_through=False)

    def draw(self, cam_x, alpha=1.0):
        x = self.x - cam_x
        if self.dead:
            self.look.draw("down", min(1.0, self.dead * 1.5), x, self.y, self.facing)
            return
        if self.hurt > 0 and int(self.hurt * 20) % 2 == 0:
            return                                     # blink while invulnerable after a hit
        if self.roll > 0:
            self.look.draw("run", (1 - self.roll / ROLL_TIME) * 0.5, x, self.y - 4, self.roll_dir,
                           distance=self.run_distance + (1 - self.roll / ROLL_TIME) * 3)
        elif self.slash:
            progress = self.slash["time"] / SLASH_TIME
            self.look.draw("swing", progress, x, self.y, self.facing, contact=SLASH_HIT / SLASH_TIME)
        elif not self.on_ground:
            self.look.draw("run", 0.25, x, self.y, self.facing, distance=1.1)
        elif self._moving:
            self.look.draw("run", self.time, x, self.y, self.facing, distance=self.run_distance)
        else:
            self.look.draw("idle", self.time, x, self.y, self.facing)

    _moving = False


class Zombie(Body):
    def __init__(self, look, x, y):
        super().__init__(x, y)
        self.look = look
        self.facing = -1
        self.state = "idle"          # idle, chase, windup, strike, recover, dead
        self.timer = 0.0
        self.time = random.random()
        self.walk = 0.0
        self.death_dir = 1

    @property
    def alive(self):
        return self.state != "dead"

    def kill(self, direction):
        self.state = "dead"
        self.timer = 0.0
        self.death_dir = direction
        self.vy = 220
        self.vx = direction * 160

    def update(self, dt, hero):
        self.time += dt
        if self.state == "dead":
            self.timer += dt
            self.x += self.vx * dt
            self.vx *= 0.9
            self.fall(dt)
            return None
        dx, dy = hero.x - self.x, hero.y - self.y
        event = None
        if self.state == "idle" and hypot(dx, dy) < 380:
            self.state = "chase"
        if self.state == "chase":
            self.facing = 1 if dx > 0 else -1
            if abs(dx) <= ZOMBIE_REACH and abs(dy) < 26:
                self.state, self.timer = "windup", ZOMBIE_WINDUP
            else:
                step = self.facing * ZOMBIE_SPEED * dt
                self.x += step
                self.walk += abs(step) / 32
        elif self.state in ("windup", "strike", "recover"):
            self.timer -= dt
            if self.timer <= 0:
                if self.state == "windup":
                    self.state, self.timer = "strike", ZOMBIE_STRIKE
                    if abs(dx) <= ZOMBIE_REACH + 6 and abs(dy) < 30 and dx * self.facing >= -4:
                        event = "hit"
                elif self.state == "strike":
                    self.state, self.timer = "recover", ZOMBIE_RECOVER
                else:
                    self.state = "chase"
        self.fall(dt)
        return event

    def draw(self, cam_x):
        x = self.x - cam_x
        if self.state == "dead":
            if self.timer < 1.2 or int(self.timer * 12) % 2 == 0:
                self.look.draw("down", min(1.0, self.timer * 2), x, self.y, -self.death_dir)
            return
        if self.state == "windup":
            self.look.draw("attack", 0.25 * (1 - self.timer / ZOMBIE_WINDUP), x, self.y, self.facing)
            ui.text_center(x, self.y + 66, "!", (255, 120, 80), 22)
        elif self.state == "strike":
            self.look.draw("attack", 0.45, x, self.y, self.facing)
        elif self.state == "recover":
            self.look.draw("attack", 0.5 + 0.5 * (1 - self.timer / ZOMBIE_RECOVER), x, self.y, self.facing)
        elif self.state == "chase":
            self.look.draw("walk", self.time, x, self.y, self.facing, distance=self.walk)
        else:
            self.look.draw("idle", self.time, x, self.y, self.facing)


class Crescent:
    """The big white slash crescent along the aim."""

    LIFE = 0.16

    def __init__(self, x, y, angle):
        self.x, self.y, self.angle = x, y, angle
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        return self.age < self.LIFE

    def draw(self, cam_x):
        fade = 1 - self.age / self.LIFE
        cx, cy = self.x - cam_x, self.y
        for ring, (radius, alpha) in enumerate(((52, 255), (48, 230), (44, 190), (40, 130), (36, 70))):
            pts = []
            for k in range(13):
                t = -SLASH_ARC + 2 * SLASH_ARC * k / 12
                width = sin(pi * k / 12)                       # thick in the middle, thin at the tips
                r = radius + 6 * width * (1 if ring == 0 else 0.6)
                pts.append((cx + cos(self.angle + t) * r, cy + sin(self.angle + t) * r))
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                pico2d.draw_line(x1, y1, x2, y2, 255, 255, 255, round(alpha * fade))


class Spark:
    """A short burst where a blow lands."""

    def __init__(self, x, y, big=False):
        self.x, self.y = x, y
        self.age = 0.0
        self.big = big

    def update(self, dt):
        self.age += dt
        return self.age < 0.18

    def draw(self, cam_x):
        p = self.age / 0.18
        scale = 1.6 if self.big else 1.0
        for dx, dy in ((-25, 8), (-15, 21), (4, 25), (22, 15), (26, -4), (12, -13), (-10, -14)):
            a, b = (0.2 + p * 0.7) * scale, (0.2 + p * 0.7 + (1 - p) * 0.5) * scale
            pico2d.draw_line(self.x - cam_x + dx * a, self.y + dy * a, self.x - cam_x + dx * b,
                             self.y + dy * b, 255, 120, 110)
        if p < 0.35:
            pico2d.draw_circle(self.x - cam_x, self.y, round(5 * scale), 255, 230, 220, filled=True)


class Game:
    def __init__(self):
        self.hero_look = SheetLook(ROOT / "assets/characters/hero")
        self.zombie_look = SheetLook(ROOT / "assets/characters/infected")
        self.background = pico2d.load_image(str(ROOT / "assets/surface_side.png"))
        self.aim = (None, None)
        self.reset()

    def reset(self):
        self.hero = Hero(self.hero_look)
        self.zombies = [Zombie(self.zombie_look, x, y) for x, y in ZOMBIE_STARTS]
        self.effects = []
        self.cam_x = 0.0
        self.hitstop = 0.0
        self.shake = 0.0
        self.slow = False
        self.slow_blend = 0.0
        self.exposure = 0.0
        self.message = "A/D 이동 · W 점프 · S 내려가기 · 좌클릭 베기 · Space 구르기 · 우클릭 시간 느리게"
        self.cleared = False
        self.restart_timer = 0.0
        self.deaths = getattr(self, "deaths", 0)

    # input ----------------------------------------------------------------
    def mouse_world(self, sx, sy):
        return sx / SCALE + self.cam_x, (HEIGHT - 1 - sy) / SCALE

    def click(self, sx, sy):
        self.aim = (sx, sy)
        wx, wy = self.mouse_world(sx, sy)
        self.hero.start_slash(wx, wy)

    def key_down(self, key, keys):
        if key == sdl2.SDLK_SPACE:
            move = keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A]
            self.hero.start_roll(move)
        elif key == sdl2.SDLK_r:
            self.reset()

    # update ---------------------------------------------------------------
    def update(self, real_dt, keys):
        self.slow_blend += (1 if self.slow and not self.hero.dead else -1) * real_dt / 0.12
        self.slow_blend = max(0.0, min(1.0, self.slow_blend))
        if self.slow and not self.hero.dead:
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
        hero = self.hero
        aim_x = self.mouse_world(*self.aim)[0] if self.aim[0] is not None else None
        hero._moving = bool(keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A])
        hero.update(real_dt, keys, aim_x)

        # the blade connects once per slash
        if hero.slash and not hero.slash["hit"] and hero.slash["time"] >= SLASH_HIT:
            hero.slash["hit"] = True
            sx, sy = hero.x, hero.y + 22
            self.effects.append(Crescent(sx, sy, hero.slash["angle"]))
            for z in self.zombies:
                if not z.alive:
                    continue
                zx, zy = z.x, z.y + 22
                d = hypot(zx - sx, zy - sy)
                diff = (atan2(zy - sy, zx - sx) - hero.slash["angle"] + pi) % (2 * pi) - pi
                if d <= SLASH_REACH + 12 and abs(diff) <= SLASH_ARC:
                    z.kill(1 if zx >= sx else -1)
                    self.effects.append(Spark(zx, zy + 4, big=True))
                    self.hitstop = max(self.hitstop, 0.07)
                    self.shake = 0.12

        for z in self.zombies:
            if z.update(world_dt, hero) == "hit" and not hero.invulnerable and not hero.dead:
                hero.hp -= 1
                hero.hurt = HURT_INVULNERABLE
                self.effects.append(Spark(hero.x, hero.y + 26))
                self.hitstop = 0.1
                self.shake = 0.2
                if hero.hp <= 0:
                    hero.dead = 0.001
                    self.deaths += 1
                    self.message = "쓰러졌다… 바로 다시 시작"
        self.effects = [e for e in self.effects if e.update(real_dt)]

        if hero.dead and hero.dead > 0.9:
            self.reset()
            return
        if not self.cleared and all(not z.alive for z in self.zombies):
            self.cleared = True
            self.message = "구역 정리! R로 다시 해 보기"
        target = hero.x - VIEW_W / 2
        self.cam_x += (max(0, min(ROOM_WIDTH - VIEW_W, target)) - self.cam_x) * min(1.0, real_dt * 8)

    # draw -----------------------------------------------------------------
    def draw(self):
        # World: drawn at VIEW_W x VIEW_H into an off-screen texture, then enlarged by SCALE
        # in one go, so images and lines are zoomed alike (chunky pixels).
        if not hasattr(self, "target"):
            self.target = sdl2.SDL_CreateTexture(canvas.renderer, sdl2.SDL_PIXELFORMAT_RGBA8888,
                                                 sdl2.SDL_TEXTUREACCESS_TARGET, VIEW_W, VIEW_H)
            sdl2.SDL_SetTextureBlendMode(self.target, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetRenderTarget(canvas.renderer, self.target)
        sdl2.SDL_SetRenderDrawColor(canvas.renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(canvas.renderer)
        canvas.canvas_height = VIEW_H
        ox = (random.uniform(-2, 2) if self.shake > 0 else 0)
        cam = self.cam_x + ox
        bw, bh = 512, 320                                   # backdrop drawn at this size
        for i in range(-1, ROOM_WIDTH // bw + 2):           # parallax: the city moves at half speed
            self.background.draw(i * bw - cam * 0.5 + bw / 2, FLOOR + bh / 2 - 62, bw, bh)
        pico2d.draw_rectangle(0, 0, VIEW_W, FLOOR, 26, 24, 28, filled=True)
        pico2d.draw_line(0, FLOOR, VIEW_W, FLOOR, 110, 100, 92)
        for left, right, top in PLATFORMS:                  # rusty steel walkways
            pico2d.draw_rectangle(left - cam, top - 8, right - cam, top, 34, 30, 30, filled=True)
            pico2d.draw_line(left - cam, top, right - cam, top, 220, 190, 140)
            pico2d.draw_line(left - cam, top - 1, right - cam, top - 1, 150, 128, 96)
            for post in range(int(left), int(right), 40):
                pico2d.draw_line(post - cam, top - 8, post - cam, FLOOR, 44, 40, 40)
        for z in self.zombies:
            z.draw(cam)
        self.hero.draw(cam)
        for e in self.effects:
            e.draw(cam)
        if self.slow_blend > 0:
            pico2d.draw_rectangle(0, 0, VIEW_W, VIEW_H, 20, 60, 70, round(80 * self.slow_blend), filled=True)
        sdl2.SDL_SetRenderTarget(canvas.renderer, None)
        canvas.canvas_height = HEIGHT
        sdl2.SDL_RenderCopy(canvas.renderer, self.target, None, sdl2.SDL_Rect(0, 0, WIDTH, HEIGHT))
        pico2d.draw_rectangle(0, HEIGHT - 50, WIDTH, HEIGHT, 10, 12, 16, 200, filled=True)
        # HUD
        ui.text(12, HEIGHT - 20, self.message, ui.ACCENT, 14)
        ui.text(12, HEIGHT - 42, "체력 " + "■ " * self.hero.hp + "□ " * (HERO_HP - self.hero.hp), ui.PARTY, 14)
        ui.text(150, HEIGHT - 42, f"피폭 {self.exposure:4.0f}%   쓰러진 횟수 {self.deaths}", (150, 230, 160), 14)


def main():
    pico2d.open_canvas(WIDTH, HEIGHT, sync=True)
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
            if event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                if event.key == sdl2.SDLK_ESCAPE:
                    running = False
                else:
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
    main()
