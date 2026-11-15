"""One area of play: the hero, the infected, the slash, time crawling (exposure), facing
vision, sound, more infected coming in through the area's entrances, and drawing it all zoomed
into the window. F2 switches the infected senses off to compare.

Infected keep arriving from every side (2026-11-14, "사방에서 오는 긴장감"): every few seconds
one comes in through an entrance the hero is not looking at, heading for the last loud noise
(a slash or a roll), and a slash makes the next one come sooner. The area is clear once all of
them are down."""

import random
from math import atan2, cos, hypot, pi, sin

import pico2d
import sdl2
from pico2d import pico2d as canvas

import hud
import ui
from hero import PICKUP_TIME
from area import BLOCKS, ENTRANCES, EXIT, EXIT_NAME, ROOM_H, ROOM_W, SUPPLIES, ZOMBIE_STARTS
from character_look import SheetLook
from condition import BANDAGE_HEAL, PANIC_RECOVER, Condition
from hero import Hero
from infected import GRAB_NEAR, GRAB_TIME, NOISE_ROLL, NOISE_SLASH, NOISE_STEP, Zombie
import infected
from settings import (CHEST, EXPOSURE_FALL, EXPOSURE_ON, EXPOSURE_RISE, HEIGHT, HERO_HP, HURT_INVULNERABLE,
                      ROLL_TIME, ROOT, SCALE, SLASH_ARC, SLASH_HIT, SLASH_REACH, SLOW_WORLD, VIEW_H,
                      VIEW_W, WIDTH)
from slash_fx import Blood, Crescent, Spark, Streak, draw_stains
from sound import Sounds
import supplies as supply_rules
from supplies import KINDS, PILL_EFFECT, Supply
from vision_cone import CONE_HALF, VisionCone, ray_hit


WAVE_TOTAL = 12              # infected in this area, the starting ones included
MAX_ALIVE = 6                # at most this many up at once
SPAWN_EVERY = (6.0, 9.0)     # s between arrivals
SPAWN_AFTER_NOISE = 1.5      # s: a slash or roll brings the next one this soon
NOISE_PULL = 5.0             # s a loud noise keeps pulling arrivals toward it
SPAWN_MIN_DIST = 240         # px: never right next to the hero
SHOVE_REACH = 46             # px a shove reaches
MUFFLED_OFFSET = 55          # px a sound heard through a wreck is misplaced by (Zomboid: +-2 tiles)


DEATH_SUMMARY = 2.2          # s the short "how you died" card shows before the area restarts
HUD_PAD = 40                 # world px the HUD bar covers at the top of the screen


class Game:
    def __init__(self):
        self.hero_look = SheetLook(ROOT / "assets/characters/hero")
        self.zombie_look = SheetLook(ROOT / "assets/characters/infected")
        self.aim = (None, None)
        self.deaths = 0
        self.vision = VisionCone(BLOCKS)    # wrecks block the light
        self.hints_shown = set()            # first-time hints, once per play session
        self.senses = True                  # F2: infected senses on/off (compare)
        self.real = True                    # F3: realistic look on/off (compare)
        infected.Zombie.show_marks = True   # "!" / "?" stay (2026-11-15 "이 부분은 넣어도 될 것 같습니다")
        infected.Zombie.blink_corpse = not self.real
        self.bag_open = False               # Tab: the bag (inventory)
        self.bag_cursor = 0
        self.look = 0.0
        self.sounds = Sounds()
        # Rendered in Blender (tools/blender/render_area.py): the ground, and a picture per wreck.
        area_dir = ROOT / "assets" / "area"
        self.ground_img = pico2d.load_image(str(area_dir / "ground.png")) if (area_dir / "ground.png").exists() else None
        self.wreck_imgs = [pico2d.load_image(str(area_dir / f"wreck_{i}.png")) if (area_dir / f"wreck_{i}.png").exists()
                           else None for i in range(len(BLOCKS))]
        self.sounds.loop("ai_wind_ruins", 0.35)            # the area's ambience (AI-made, if present)
        fixed = random.Random(4)            # the same cracks every time, without fixing the game's own luck
        self.cracks = [(fixed.uniform(0, ROOM_W), fixed.uniform(0, ROOM_H), fixed.uniform(-1, 1))
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
        self.message = "물자를 챙겨 지하철 입구로 · E 줍기/나가기 · 1 붕대 · 좌클릭 베기 · Space 구르기 · F3 연출 비교"
        self.cleared = False
        self.to_spawn = WAVE_TOTAL - len(self.zombies)
        self.spawn_in = random.uniform(*SPAWN_EVERY)
        self.clock = 0.0
        self.loud = None             # (x, y, time) of the last slash or roll
        self.was_slow = False
        self.hero_steps = 0
        self.siren_in = random.uniform(15, 30)
        self.supplies = [Supply(x, y, kind) for x, y, kind in SUPPLIES if EXPOSURE_ON or kind != "pill"]
        self.condition = Condition()         # tension, wounds (status icons)
        self.death_cause, self.death_time = "", 0.0
        self.stains = []             # blood on the ground (realistic look)
        self.bag_open = False
        self.bag_cursor = 0
        self.message_at = 0.0
        self.bag = {kind: 0 for kind in KINDS}
        self.kills = 0
        self.left = False            # reached the exit: the area is done

    def mouse_world(self, sx, sy):
        return sx / SCALE + self.cam[0], (HEIGHT - 1 - sy) / SCALE + self.cam[1]

    def right_click(self, sx, sy):
        """Shove: infected right in front reel (or fall) and any attack they wind up is broken off."""
        self.aim = (sx, sy)
        hero = self.hero
        if not hero.start_shove(*self.mouse_world(sx, sy)):
            return
        self.sounds.play("roll", 0.5)
        for z in self.zombies:
            if not z.alive or z.state in ("down",):
                continue
            diff = (atan2(z.y - hero.y, z.x - hero.x) - hero.shove_angle + pi) % (2 * pi) - pi
            if hypot(z.x - hero.x, z.y - hero.y) <= SHOVE_REACH and abs(diff) <= 0.9:
                z.shoved(hero.x, hero.y)
                self.sounds.play("slash_hit", 0.35, at=(z.x, z.y))
                self.message = "넘어뜨렸다! 지금 베면 확실하다" if z.state == "down" else "밀쳐냈다"
        if self.senses:
            self.make_noise(NOISE_STEP)

    def unaware_in_reach(self, angle):
        """Infected within the slash that have not spotted the hero (Zomboid: a blow on an
        unaware zombie is a sure, quiet finisher)."""
        hero, found = self.hero, []
        for z in self.zombies:
            if z.alive and z.helpless:
                diff = (atan2(z.y - hero.y, z.x - hero.x) - angle + pi) % (2 * pi) - pi
                if hypot(z.x - hero.x, z.y - hero.y) <= SLASH_REACH + 30 and abs(diff) <= SLASH_ARC:
                    found.append(z)
        return found

    def click(self, sx, sy):
        self.aim = (sx, sy)
        before = self.hero.slash
        self.hero.start_slash(*self.mouse_world(sx, sy))
        if self.hero.slash is not None and self.hero.slash is not before:
            self.hero.slash["quiet"] = bool(self.unaware_in_reach(self.hero.slash["angle"]))
            self.sounds.play("slash", 0.45 if self.hero.slash["quiet"] else 0.8)

    def use(self, kind):
        """Use one supply from the bag (keys 1/2 or Enter in the bag)."""
        if self.hero.dead or not self.bag.get(kind):
            return
        if kind == "bandage" and (self.hero.hp < HERO_HP or self.condition.injuries):
            self.bag[kind] -= 1
            treated = self.condition.treat()
            before = self.hero.hp
            self.hero.hp = min(HERO_HP, self.hero.hp + BANDAGE_HEAL)
            gained = self.hero.hp - before
            self.message = "붕대를 감았다" + (f" ({treated} 치료)" if treated else "") +                 (f" 체력 +{gained:.0f}%" if gained >= 1 else "")
            self.sounds.play("pickup", 0.6)
        elif kind == "pill" and EXPOSURE_ON:
            self.bag[kind] -= 1
            self.exposure = max(0.0, self.exposure - PILL_EFFECT)
            self.message = f"피폭 억제제를 먹었다 (피폭 -{PILL_EFFECT:.0f})"
            self.sounds.play("pickup", 0.6)
        elif kind == "bandage":
            self.message = "다친 곳이 없다"

    def bag_key(self, key):
        items = hud.bag_items(self)
        cols = hud.BAG_COLS                                # a grid again (the reference picture)
        moves = {sdl2.SDLK_LEFT: -1, sdl2.SDLK_RIGHT: 1, sdl2.SDLK_UP: -cols, sdl2.SDLK_DOWN: cols,
                 sdl2.SDLK_a: -1, sdl2.SDLK_d: 1, sdl2.SDLK_w: -cols, sdl2.SDLK_s: cols}
        if key in (sdl2.SDLK_TAB, sdl2.SDLK_ESCAPE):
            self.bag_open = False
        elif key in moves:
            self.bag_cursor = (self.bag_cursor + moves[key]) % (hud.BAG_COLS * hud.BAG_ROWS)
        elif key == sdl2.SDLK_f:                                         # take all nearby
            taken = 0
            for item in hud.nearby_items(self):
                if supply_rules.bag_weight(self.bag) + supply_rules.weight_of(item.kind) > supply_rules.BAG_CAPACITY + 1e-6:
                    break
                item.taken = True
                self.bag[item.kind] += 1
                taken += 1
            self.message = f"물건 {taken}개를 챙겼다" if taken else "더 챙길 수 없다"
            if taken:
                self.sounds.play("pickup", 0.8)
                if self.senses:
                    self.make_noise(supply_rules.PICK_NOISE)
        elif key in (sdl2.SDLK_RETURN, sdl2.SDLK_KP_ENTER) and self.bag_cursor < len(items):
            self.use(items[self.bag_cursor][0])
        elif key == sdl2.SDLK_x and self.bag_cursor < len(items):        # drop one at the hero's feet
            kind = items[self.bag_cursor][0]
            self.bag[kind] -= 1
            self.supplies.append(Supply(self.hero.x + 10, self.hero.y - 4, kind))
            self.message = f"{supply_rules.with_object_particle(KINDS[kind][0])} 내려놓았다"
            self.bag_cursor = min(self.bag_cursor, max(0, len(hud.bag_items(self)) - 1))

    def key_down(self, key, keys):
        if self.bag_open:                                  # the bag takes the keys while it is open
            self.bag_key(key)
            return
        if key == sdl2.SDLK_TAB and not self.left and not self.hero.dead:
            self.bag_open = True
            self.slow = False
            return
        if key == sdl2.SDLK_SPACE:
            self.hero.start_roll(keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A],
                                 keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S])
            if self.hero.roll >= ROLL_TIME:
                self.sounds.play("roll", 0.6)
        elif key == sdl2.SDLK_r:
            self.reset()
        elif key == sdl2.SDLK_e and not self.left and not self.hero.dead:
            self.interact()
        elif key == sdl2.SDLK_1:
            self.use("bandage")
        elif key == sdl2.SDLK_2:
            self.use("pill")
        elif key == sdl2.SDLK_F3:
            self.real = not self.real
            infected.Zombie.blink_corpse = not self.real
            self.message = "사실적 연출 켬: 피, 시체, 어두운 색" if self.real \
                else "사실적 연출 끔: 예전 연출(반달 궤적, 불꽃)"
        elif key == sdl2.SDLK_F2:
            self.senses = not self.senses
            self.reset()
            self.message = ("피폭체 감각 켬: 보고 듣고 찾음, 시야 밖 공격은 예고가 짧음" if self.senses
                            else "피폭체 감각 끔: 예전 규칙(300px 안이면 무조건 쫓아옴)")

    def hint(self, key, text):
        """A one-time tip (2026-11-16: lower the entry barrier - Zomboid's biggest complaint)."""
        if key not in self.hints_shown:
            self.hints_shown.add(key)
            self.message = text

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
        if item is None or self.hero.pickup > 0 or self.hero.slash or self.hero.roll > 0:
            return
        if supply_rules.bag_weight(self.bag) + supply_rules.weight_of(item.kind) > supply_rules.BAG_CAPACITY + 1e-6:
            self.message = "배낭이 무겁다 (Tab에서 X로 버리기)"
            return
        self.hero.pickup = PICKUP_TIME                     # a short crouch to pick it up
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
        hx, hy = self.hero.x, self.hero.y
        for z in self.zombies:
            if not z.alive:
                continue
            # Zomboid: a sound heard through a wreck or wall can't be placed exactly - the
            # infected heads for a spot off by up to MUFFLED_OFFSET px (open ground: exact).
            dist = hypot(hx - z.x, hy - z.y)
            if dist > 1 and ray_hit(z.x, z.y, (hx - z.x) / dist, (hy - z.y) / dist, BLOCKS) < dist:
                ox, oy = random.uniform(-1, 1) * MUFFLED_OFFSET, random.uniform(-1, 1) * MUFFLED_OFFSET
                z.hear(hx + ox, hy + oy, radius, origin=(hx, hy))
            else:
                z.hear(hx, hy, radius)

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
        if self.left or self.bag_open:                     # summary or bag open: the world waits
            return
        self.clock += real_dt
        if self.clock > 1.0:
            self.hint("sneak", "Ctrl 살금살금 · 소리가 피폭체를 부른다 · 못 본 피폭체는 조용히 벨 수 있다")
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
            self.sounds.play("step", 0.1 if hero.sneaking else 0.25)
        if self.aim[0] is not None:          # the hero looks toward the mouse
            ax, ay = self.mouse_world(*self.aim)
            self.look = atan2(ay - (hero.y + CHEST), ax - hero.x)
        else:
            self.look = 0.0 if hero.facing > 0 else pi

        if hero.slash and not hero.slash["hit"] and hero.slash["time"] >= SLASH_HIT:
            hero.slash["hit"] = True
            sx, sy = hero.x, hero.y + CHEST
            self.effects.append((Streak if self.real else Crescent)(sx, sy, hero.slash["angle"]))
            for z in self.zombies:
                if not z.alive:
                    continue
                zx, zy = z.x, z.y + CHEST
                diff = (atan2(zy - sy, zx - sx) - hero.slash["angle"] + pi) % (2 * pi) - pi
                if hypot(zx - sx, zy - sy) <= SLASH_REACH + 12 and abs(diff) <= SLASH_ARC:
                    unaware = z.helpless
                    z.kill(zx - sx, zy - sy)
                    self.kills += 1
                    if unaware:                                  # finisher: a clean, quiet kill
                        self.message = "들키기 전에 조용히 처리했다"
                        self.effects.append(Blood(zx, zy - 4, atan2(zy - sy, zx - sx), 26))
                        self.hitstop = max(self.hitstop, 0.09)
                    self.sounds.play("slash_hit", 0.9)
                    self.sounds.play("infected_down", 0.6, at=(z.x, z.y))
                    if self.real:
                        self.effects.append(Blood(zx, zy - 6, atan2(zy - sy, zx - sx), 18))
                        ang = atan2(zy - sy, zx - sx)          # a pool where the body will lie
                        for k in range(9):
                            d = random.uniform(4, 22)
                            self.stains.append((z.x + cos(ang) * d + random.uniform(-6, 6),
                                                z.y + sin(ang) * d * 0.5 + random.uniform(-4, 3),
                                                random.randint(3, 6)))
                        self.hitstop, self.shake = max(self.hitstop, 0.035), 0.05
                    else:
                        self.effects.append(Spark(zx, zy + 4, big=True))
                        self.hitstop, self.shake = max(self.hitstop, 0.07), 0.12

        if self.senses and not hero.dead:          # the hero's noise: steps, rolls, slashes
            if hero.slash and hero.slash["time"] <= real_dt:
                self.make_noise(NOISE_STEP if hero.slash.get("quiet") else NOISE_SLASH)
            elif hero.roll > 0 and hero.roll >= ROLL_TIME - real_dt:
                self.make_noise(NOISE_ROLL)
            elif hero.moving:
                self.make_noise(NOISE_STEP * (0.4 if hero.sneaking else 1.0))   # sneaking is quiet
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
                    z.spotted = infected.SPOTTED_TIME                         # "!" - it spotted the hero
                    self.hint("spotted", "들켰다! 우클릭으로 밀치고, 넘어지면 베어라")
                    self.sounds.play("ai_infected_scream", 0.6, at=(z.x, z.y))
                elif z.state == "windup":
                    self.sounds.play("warn", 0.9, at=(z.x, z.y))
                elif z.state == "alert":
                    self.sounds.play("alert", 0.8, at=(z.x, z.y))
            elif z.alive and int(z.walk) != steps:
                self.sounds.play("infected_step", 0.35, at=(z.x, z.y))
            if event == "hit" and not hero.invulnerable and not hero.dead:
                self.sounds.play("hurt", 1.0)
                hero.take_blow()                              # slowed, more with every blow
                wound, damage = self.condition.wound()        # the blow's kind sets how much it takes
                hero.hp = max(0.0, hero.hp - damage)
                self.message = f"{wound}! 체력 -{damage}%"
                if wound != "긁힘":
                    self.hint("bleed", f"{wound}: 피를 흘린다 · 1 또는 Tab에서 붕대로 멈춰라")
                hero.hurt = HURT_INVULNERABLE
                others = sum(1 for o in self.zombies if o is not z and o.alive
                             and hypot(o.x - hero.x, o.y - hero.y) <= GRAB_NEAR)
                if self.senses and others and hero.hp > 0:
                    hero.grabbed = GRAB_TIME             # Zomboid's drag-down: two on him hold him
                    hero.slash = None
                    self.message = "붙잡혔다! Space로 구르면 빠져나감"
                    self.sounds.play("grab", 1.0)
                if self.real:
                    self.effects.append(Blood(hero.x, hero.y + 16, atan2(hero.y - z.y, hero.x - z.x), 10))
                    self.hitstop, self.shake = 0.06, 0.12
                else:
                    self.effects.append(Spark(hero.x, hero.y + 26))
                    self.hitstop, self.shake = 0.1, 0.2
                if hero.hp <= 0:
                    hero.dead = 0.001
                    self.deaths += 1
                    self.death_cause = "피폭체에게 당했다"
                    self.death_time = self.clock
        bled = self.condition.update(real_dt, hero, self.zombies)
        if bled and not hero.dead:                             # bleeding drains health until bandaged
            hero.hp = max(0.0, hero.hp - bled)
            if hero.hp <= 0:
                self.death_cause, self.death_time = "피를 너무 많이 흘렸다", self.clock
                hero.dead = 0.001
                self.deaths += 1
        if self.condition.panic and hero.slash_cooldown > 0 and not getattr(hero, "_panic_slowed", False):
            hero.slash_cooldown *= PANIC_RECOVER               # shaking hands: slower to swing again
            hero._panic_slowed = True
        if hero.slash_cooldown <= 0:
            hero._panic_slowed = False
        self.vision.scale = self.condition.view_scale()      # panic narrows the view
        self.effects = [e for e in self.effects if e.update(real_dt)]
        for e in self.effects:
            if isinstance(e, Blood):
                self.stains.extend(e.landed())
        if self.message != getattr(self, "_shown", None):
            self._shown, self.message_at = self.message, self.clock
        if hero.dead > DEATH_SUMMARY:
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
        if self.ground_img is not None:                    # the rendered street
            self.ground_img.draw(ROOM_W / 2 - cx, ROOM_H / 2 - cy)
        else:
            self.draw_plain_ground(cx, cy)
        self.draw_area_edges(cx, cy)
        self.draw_world(cx, cy)

    def draw_plain_ground(self, cx, cy):
        """The old drawn asphalt, used when the rendered ground is missing."""
        for lane in range(80, ROOM_H, 160):
            for x0 in range(0, ROOM_W, 60):
                pico2d.draw_rectangle(x0 - cx, lane - cy, x0 + 30 - cx, lane + 2 - cy, 120, 110, 80, filled=True)
        for x, y, t in self.cracks:
            pico2d.draw_line(x - cx, y - cy, x + 14 - cx, y + 10 * t - cy, 20, 20, 24)

    def draw_area_edges(self, cx, cy):
        pico2d.draw_rectangle(-cx, -cy, ROOM_W - cx, ROOM_H - cy, 70, 64, 60)
        for (x, y), side in ENTRANCES:                    # alley mouths and doorways
            w, d = (22, 34) if side in ("left", "right") else (34, 22)
            gx = {"left": -d, "right": ROOM_W - 2}.get(side, x - w / 2 - 6)
            gy = {"top": ROOM_H - 2, "bottom": -d}.get(side, y - w / 2 - 6)
            gw, gh = (d + 2, w + 12) if side in ("left", "right") else (w + 12, d + 2)
            pico2d.draw_rectangle(gx - cx, gy - cy, gx + gw - cx, gy + gh - cy, 12, 12, 16, filled=True)

    def draw_world(self, cx, cy):
        """Everything on the ground over the floor, the darkness, then the screen UI."""
        l, b, r, t = EXIT                                  # subway stairs going down
        pico2d.draw_rectangle(l - cx, b - cy, r - cx, t - cy, 18, 20, 22, filled=True)
        for i in range(5):
            pico2d.draw_line(l + 4 - cx, b + 6 + i * 12 - cy, r - 4 - cx, b + 6 + i * 12 - cy, 60, 64, 66)
        pico2d.draw_rectangle(l - cx, b - cy, r - cx, t - cy, 90, 96, 92)
        draw_stains(self.stains, cx, cy)
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
            if kind == "block" and self.wreck_imgs[BLOCKS.index(obj)] is not None:
                img = self.wreck_imgs[BLOCKS.index(obj)]           # rendered wreck, standing on its block
                l, b, r, t = obj
                img.draw((l + r) / 2 - cx, b - 3 + img.h / 2 - cy)
            elif kind == "block":
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
        if self.real:                                      # a muted, colder tone over everything
            pico2d.draw_rectangle(0, 0, VIEW_W, VIEW_H, 26, 30, 34, 70, filled=True)
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
        hud.draw_hud(self)
        if self.bag_open:
            hud.draw_inventory(self)
        if self.left:
            hud.draw_summary(self)
        if self.hero.dead > 0.4:
            hud.draw_death(self)
