"""One area of play: the hero, the infected, the slash, time crawling (exposure), facing
vision, sound, more infected coming in through the area's entrances, and drawing it all zoomed
into the window. F2 switches the infected senses off to compare.

Infected keep arriving from every side (2026-11-14, "사방에서 오는 긴장감"): every few seconds
one comes in through an entrance the hero is not looking at, heading for the last loud noise
(a slash or a roll), and a slash makes the next one come sooner. The area is clear once all of
them are down."""

import random
from math import atan2, hypot, pi

import pico2d
import sdl2
from pico2d import pico2d as canvas

import ui
from area import BLOCKS, ENTRANCES, EXIT, EXIT_NAME, ROOM_H, ROOM_W, SUPPLIES, ZOMBIE_STARTS
from character_look import SheetLook
from hero import Hero
from infected import GRAB_NEAR, GRAB_TIME, NOISE_ROLL, NOISE_SLASH, NOISE_STEP, Zombie
from settings import (CHEST, EXPOSURE_FALL, EXPOSURE_RISE, HEIGHT, HERO_HP, HURT_INVULNERABLE, ROLL_TIME,
                      ROOT, SCALE, SLASH_ARC, SLASH_HIT, SLASH_REACH, SLOW_WORLD, VIEW_H, VIEW_W, WIDTH)
from slash_fx import Crescent, Spark
from sound import Sounds
import supplies as supply_rules
from supplies import KINDS, PILL_EFFECT, Supply
from vision_cone import CONE_HALF, VisionCone


WAVE_TOTAL = 12              # infected in this area, the starting ones included
MAX_ALIVE = 6                # at most this many up at once
SPAWN_EVERY = (6.0, 9.0)     # s between arrivals
SPAWN_AFTER_NOISE = 1.5      # s: a slash or roll brings the next one this soon
NOISE_PULL = 5.0             # s a loud noise keeps pulling arrivals toward it
SPAWN_MIN_DIST = 240         # px: never right next to the hero


HUD_PAD = 40                 # world px the HUD bar covers at the top of the screen


class Game:
    def __init__(self):
        self.hero_look = SheetLook(ROOT / "assets/characters/hero")
        self.zombie_look = SheetLook(ROOT / "assets/characters/infected")
        self.aim = (None, None)
        self.deaths = 0
        self.vision = VisionCone(BLOCKS)    # wrecks block the light
        self.senses = True                  # F2: infected senses on/off (compare)
        self.look = 0.0
        self.sounds = Sounds()
        self.sounds.loop("ai_wind_ruins", 0.35)            # the area's ambience (AI-made, if present)
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
        self.message = "물자를 챙겨 지하철 입구로 · E 줍기/나가기 · 1 붕대 · 2 억제제 · 좌클릭 베기 · Space 구르기 · 우클릭 느리게"
        self.cleared = False
        self.to_spawn = WAVE_TOTAL - len(self.zombies)
        self.spawn_in = random.uniform(*SPAWN_EVERY)
        self.clock = 0.0
        self.loud = None             # (x, y, time) of the last slash or roll
        self.was_slow = False
        self.hero_steps = 0
        self.siren_in = random.uniform(15, 30)
        self.supplies = [Supply(x, y, kind) for x, y, kind in SUPPLIES]
        self.bag = {kind: 0 for kind in KINDS}
        self.kills = 0
        self.left = False            # reached the exit: the area is done

    def mouse_world(self, sx, sy):
        return sx / SCALE + self.cam[0], (HEIGHT - 1 - sy) / SCALE + self.cam[1]

    def click(self, sx, sy):
        self.aim = (sx, sy)
        before = self.hero.slash
        self.hero.start_slash(*self.mouse_world(sx, sy))
        if self.hero.slash is not None and self.hero.slash is not before:
            self.sounds.play("slash", 0.8)

    def key_down(self, key, keys):
        if key == sdl2.SDLK_SPACE:
            self.hero.start_roll(keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A],
                                 keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S])
            if self.hero.roll >= ROLL_TIME:
                self.sounds.play("roll", 0.6)
        elif key == sdl2.SDLK_r:
            self.reset()
        elif key == sdl2.SDLK_e and not self.left and not self.hero.dead:
            self.interact()
        elif key == sdl2.SDLK_1 and self.bag["bandage"] and self.hero.hp < HERO_HP and not self.hero.dead:
            self.bag["bandage"] -= 1
            self.hero.hp += 1
            self.message = "붕대를 감았다 (체력 +1)"
            self.sounds.play("pickup", 0.6)
        elif key == sdl2.SDLK_2 and self.bag["pill"] and not self.hero.dead:
            self.bag["pill"] -= 1
            self.exposure = max(0.0, self.exposure - PILL_EFFECT)
            self.message = f"피폭 억제제를 먹었다 (피폭 -{PILL_EFFECT:.0f})"
            self.sounds.play("pickup", 0.6)
        elif key == sdl2.SDLK_F2:
            self.senses = not self.senses
            self.reset()
            self.message = ("피폭체 감각 켬: 보고 듣고 찾음, 시야 밖 공격은 예고가 짧음" if self.senses
                            else "피폭체 감각 끔: 예전 규칙(300px 안이면 무조건 쫓아옴)")

    def near_exit(self):
        l, b, r, t = EXIT
        return l - 14 <= self.hero.x <= r + 14 and b - 14 <= self.hero.y <= t + 14

    def interact(self):
        """E: leave through the exit, or pick up the nearest supply (rummaging is heard)."""
        if self.near_exit():
            self.left = True
            self.slow = False
            self.message = "구역을 빠져나왔다 · R 다시"
            self.sounds.play("exit", 0.8)
            return
        item = supply_rules.nearest(self.supplies, self.hero.x, self.hero.y)
        if item is None:
            return
        item.taken = True
        self.bag[item.kind] += 1
        self.message = f"{supply_rules.with_object_particle(item.name)} 챙겼다" + (f" ({supply_rules.USE_KEYS[item.kind]}로 사용)"
                                                   if item.kind in supply_rules.USE_KEYS else "")
        self.sounds.play("pickup", 0.8)
        if self.senses:
            self.make_noise(supply_rules.PICK_NOISE)

    def hero_sees(self, zombie):
        """Is the infected inside the hero's view cone? (The small lit circle around the body
        does not count: what comes from the side or behind is still a blind-side attack.)"""
        off = abs((atan2(zombie.y - self.hero.y, zombie.x - self.hero.x) - self.look + pi) % (2 * pi) - pi)
        return off <= CONE_HALF

    def make_noise(self, radius):
        if radius >= NOISE_ROLL:                          # loud: pulls the next arrivals here
            if self.loud is None or self.clock - self.loud[2] > 0.5:
                self.spawn_in = min(self.spawn_in, SPAWN_AFTER_NOISE)
            self.loud = (self.hero.x, self.hero.y, self.clock)
        for z in self.zombies:
            if z.alive:
                z.hear(self.hero.x, self.hero.y, radius)

    def spawn(self):
        """One more infected through an entrance the hero is not looking at, far enough away."""
        hero = self.hero
        far = [pos for pos, _ in ENTRANCES if hypot(pos[0] - hero.x, pos[1] - hero.y) >= SPAWN_MIN_DIST]
        unseen = [pos for pos in far if abs((atan2(pos[1] - hero.y, pos[0] - hero.x) - self.look + pi)
                                            % (2 * pi) - pi) > CONE_HALF]
        choices = unseen or far
        if not choices:
            return False
        x, y = random.choice(choices)
        z = Zombie(self.zombie_look, x, y)
        if self.senses:
            recent = self.loud is not None and self.clock - self.loud[2] <= NOISE_PULL
            target = (self.loud[0], self.loud[1]) if recent else (random.uniform(200, ROOM_W - 200),
                                                                  random.uniform(150, ROOM_H - 150))
            z.state, z.target, z.memory = "search", target, 8.0
        self.zombies.append(z)
        self.to_spawn -= 1
        self.sounds.play("alert", 0.7, at=(x, y))          # heard coming in, maybe unseen
        return True

    def update(self, real_dt, keys):
        hero = self.hero
        if self.left:                                      # out of the area: only the summary shows
            return
        self.clock += real_dt
        self.sounds.listener = (hero.x, hero.y)
        if self.slow != self.was_slow and not hero.dead:
            self.sounds.play("slow_in" if self.slow else "slow_out", 0.6)
        self.was_slow = self.slow
        self.slow_blend = max(0.0, min(1.0, self.slow_blend + (1 if self.slow and not hero.dead else -1)
                                       * real_dt / 0.12))
        if self.slow and not hero.dead:
            self.exposure = min(100.0, self.exposure + EXPOSURE_RISE * real_dt)
            if self.exposure >= 100:
                self.slow = False
                self.message = "피폭 한계! 시간이 돌아옵니다"
                self.sounds.play("exposure_limit", 0.8)
        else:
            self.exposure = max(0.0, self.exposure - EXPOSURE_FALL * real_dt)
        self.shake = max(0.0, self.shake - real_dt)
        if self.hitstop > 0:
            self.hitstop -= real_dt
            return
        world_dt = real_dt * (1 + (SLOW_WORLD - 1) * self.slow_blend)
        aim_x = self.mouse_world(*self.aim)[0] if self.aim[0] is not None else None
        hero.update(real_dt, keys, aim_x)
        if int(hero.run_distance) != self.hero_steps:
            self.hero_steps = int(hero.run_distance)
            self.sounds.play("step", 0.25)
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
                    self.kills += 1
                    self.sounds.play("slash_hit", 0.9)
                    self.sounds.play("infected_down", 0.6, at=(z.x, z.y))
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
            state, steps = z.state, int(z.walk)
            event = z.update(world_dt, hero, self)
            if z.alive and z.state in ("chase", "search", "poised"):   # they groan as they come
                z.groan_in = getattr(z, "groan_in", random.uniform(0.5, 3.0)) - world_dt
                if z.groan_in <= 0:
                    self.sounds.play(random.choice(("ai_infected_groan_1", "ai_infected_groan_2")), 0.55,
                                     at=(z.x, z.y))
                    z.groan_in = random.uniform(3.0, 7.0)
            if z.state != state:
                if z.state == "chase" and state in ("idle", "alert", "search"):
                    self.sounds.play("ai_infected_scream", 0.6, at=(z.x, z.y))   # it spotted the hero
                elif z.state == "windup":
                    self.sounds.play("warn", 0.9, at=(z.x, z.y))
                elif z.state == "alert":
                    self.sounds.play("alert", 0.8, at=(z.x, z.y))
            elif z.alive and int(z.walk) != steps:
                self.sounds.play("infected_step", 0.35, at=(z.x, z.y))
            if event == "hit" and not hero.invulnerable and not hero.dead:
                self.sounds.play("hurt", 1.0)
                hero.hp -= 1
                hero.hurt = HURT_INVULNERABLE
                others = sum(1 for o in self.zombies if o is not z and o.alive
                             and hypot(o.x - hero.x, o.y - hero.y) <= GRAB_NEAR)
                if self.senses and others and hero.hp > 0:
                    hero.grabbed = GRAB_TIME             # Zomboid's drag-down: two on him hold him
                    hero.slash = None
                    self.message = "붙잡혔다! Space로 구르면 빠져나감"
                    self.sounds.play("grab", 1.0)
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
        self.siren_in -= real_dt
        if self.siren_in <= 0:                             # a siren far away now and then
            self.sounds.play("ai_siren_far", 0.25)
            self.siren_in = random.uniform(30, 50)
        if self.to_spawn > 0 and not hero.dead:
            self.spawn_in -= world_dt
            if self.spawn_in <= 0 and sum(z.alive for z in self.zombies) < MAX_ALIVE:
                self.spawn()
                self.spawn_in = random.uniform(*SPAWN_EVERY)
        if not self.cleared and self.to_spawn == 0 and all(not z.alive for z in self.zombies):
            self.cleared = True
            self.message = "구역 정리! R로 다시 해 보기"
        # the camera may go HUD_PAD past the top edge so nothing up there hides under the HUD bar
        for i, (pos, view, room) in enumerate(((hero.x, VIEW_W, ROOM_W), (hero.y, VIEW_H, ROOM_H + HUD_PAD))):
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
        for (x, y), side in ENTRANCES:                    # alley mouths and doorways
            w, d = (22, 34) if side in ("left", "right") else (34, 22)
            gx = {"left": -d, "right": ROOM_W - 2}.get(side, x - w / 2 - 6)
            gy = {"top": ROOM_H - 2, "bottom": -d}.get(side, y - w / 2 - 6)
            gw, gh = (d + 2, w + 12) if side in ("left", "right") else (w + 12, d + 2)
            pico2d.draw_rectangle(gx - cx, gy - cy, gx + gw - cx, gy + gh - cy, 12, 12, 16, filled=True)
        l, b, r, t = EXIT                                  # subway stairs going down
        pico2d.draw_rectangle(l - cx, b - cy, r - cx, t - cy, 18, 20, 22, filled=True)
        for i in range(5):
            pico2d.draw_line(l + 4 - cx, b + 6 + i * 12 - cy, r - 4 - cx, b + 6 + i * 12 - cy, 60, 64, 66)
        pico2d.draw_rectangle(l - cx, b - cy, r - cx, t - cy, 90, 96, 92)
        near_item = supply_rules.nearest(self.supplies, self.hero.x, self.hero.y)
        for s in self.supplies:
            if not s.taken:
                s.draw(cx, cy, near=s is near_item and not self.near_exit())
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
        el, eb, er, _ = EXIT                               # the green exit sign (in front) stays lit in the dark
        ex, ey = (el + er) / 2 - cx, eb - 12 - cy
        pico2d.draw_rectangle(ex - 34, ey - 7, ex + 34, ey + 9, 30, 120, 70, filled=True)
        ui.text_center(ex, ey + 1, EXIT_NAME, (220, 255, 225), 11)
        if self.near_exit() and not self.left:
            ui.text_center(self.hero.x - cx, self.hero.y - cy + 74, "E 나가기", (220, 255, 225), 12)
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
        left = self.to_spawn + sum(z.alive for z in self.zombies)
        ui.text(110, HEIGHT - 42, f"피폭 {self.exposure:3.0f}%  남은 피폭체 {left}  쓰러진 횟수 {self.deaths}",
                (150, 230, 160), 14)
        ui.text(470, HEIGHT - 42, f"붕대 {self.bag['bandage']}  억제제 {self.bag['pill']}  통조림 {self.bag['can']}",
                (230, 220, 180), 14)
        if self.left:                                      # area summary
            pico2d.draw_rectangle(WIDTH / 2 - 190, HEIGHT / 2 - 80, WIDTH / 2 + 190, HEIGHT / 2 + 80,
                                  10, 12, 16, 230, filled=True)
            lines = [(f"{EXIT_NAME}으로 빠져나왔다", ui.ACCENT),
                     (f"챙긴 물자: 붕대 {self.bag['bandage']} · 억제제 {self.bag['pill']} · 통조림 {self.bag['can']}",
                      (230, 220, 180)),
                     (f"쓰러뜨린 피폭체 {self.kills} · 피폭 {self.exposure:.0f}%", (150, 230, 160)),
                     ("다음 구역(지하철)은 3단계에서 · R 다시", (180, 180, 190))]
            for i, (line, colour) in enumerate(lines):
                ui.text_center(WIDTH / 2, HEIGHT / 2 + 48 - i * 32, line, colour, 16 if i == 0 else 14)
