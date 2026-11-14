"""One area of play: the hero, the infected, the slash, time crawling (exposure), facing
vision, and drawing it all zoomed into the window. F2 switches the infected senses off to compare."""

import random
from math import atan2, hypot, pi

import pico2d
import sdl2
from pico2d import pico2d as canvas

import ui
from area import BLOCKS, ROOM_H, ROOM_W, ZOMBIE_STARTS
from character_look import SheetLook
from hero import Hero
from infected import GRAB_NEAR, GRAB_TIME, NOISE_ROLL, NOISE_SLASH, NOISE_STEP, Zombie
from settings import (CHEST, EXPOSURE_FALL, EXPOSURE_RISE, HEIGHT, HERO_HP, HURT_INVULNERABLE, ROLL_TIME,
                      ROOT, SCALE, SLASH_ARC, SLASH_HIT, SLASH_REACH, SLOW_WORLD, VIEW_H, VIEW_W, WIDTH)
from slash_fx import Crescent, Spark
from vision_cone import CONE_HALF, VisionCone


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
            e.draw(cx, cy)
        self.vision.draw((self.hero.x, self.hero.y), self.look, (self.hero.x - cx, self.hero.y + CHEST - cy),
                         VIEW_W, VIEW_H)
        if self.slow_blend > 0:
            pico2d.draw_rectangle(0, 0, VIEW_W, VIEW_H, 20, 60, 70, round(80 * self.slow_blend), filled=True)
        sdl2.SDL_SetRenderTarget(canvas.renderer, None)
        canvas.canvas_height = HEIGHT
        sdl2.SDL_RenderCopy(canvas.renderer, self.target, None, sdl2.SDL_Rect(0, 0, WIDTH, HEIGHT))
        pico2d.draw_rectangle(0, HEIGHT - 50, WIDTH, HEIGHT, 10, 12, 16, 200, filled=True)
        ui.text(12, HEIGHT - 20, self.message, ui.ACCENT, 14)
        ui.text(12, HEIGHT - 42, "체력", ui.PARTY, 14)
        for i in range(HERO_HP):                 # boxes drawn, the font has no square glyphs
            pico2d.draw_rectangle(52 + i * 18, HEIGHT - 48, 64 + i * 18, HEIGHT - 36, 230, 90, 80,
                                  filled=i < self.hero.hp)
        ui.text(150, HEIGHT - 42, f"피폭 {self.exposure:4.0f}%   쓰러진 횟수 {self.deaths}", (150, 230, 160), 14)
