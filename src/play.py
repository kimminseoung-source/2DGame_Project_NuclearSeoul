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

import bag_grid
import bag_screen
import dev_tools
from director import Director
from daylight import Daylight
import daylight as daylight_rules
import survivors
import weapons
from weapons import BODY_CONTACT
import hud
import pixel_ui as px
import stamina as stamina_rules
import ui
from hero import PICKUP_TIME
import area
from area import (BLOCK_LOOKS, BLOCKS, ENTRANCES, EXIT, EXIT_NAME, GROUND, ROOM_H, ROOM_W, SUPPLIES,
                  WEAPONS_LYING, ZOMBIE_STARTS)
from character_look import DirLook, SheetLook

HERO_PX = "hero_px40"     # PixelLab hero folder: hero_px (32 canvas, 29 px tall) or hero_px40 (40 canvas, 36 px)
from condition import BANDAGE_HEAL, PANIC_RECOVER, Condition
from hero import Hero
from infected import GRAB_NEAR, GRAB_TIME, NOISE_ROLL, NOISE_SLASH, NOISE_STEP, Zombie
import infected
from settings import (CHEST, EXPOSURE_FALL, EXPOSURE_ON, EXPOSURE_RISE, HEIGHT, HERO_HP, HURT_INVULNERABLE,
                      ROLL_TIME, ROOT, SLOW_WORLD, WIDTH,
                      ZOOM_DEFAULT, ZOOM_STEPS, AREA_DIR, DOT, DOT_LOOK, LOOK_SUFFIX)
from slash_fx import Blood, Crescent, Spark, SpriteFx, Streak, Tracer, draw_stains
from sound import Sounds
import supplies as supply_rules
from supplies import KINDS, PILL_EFFECT, Supply
from vision_cone import CONE_HALF, VisionCone, ray_hit


WAVE_TOTAL = 12              # infected in this area, the starting ones included
SPAWN_AFTER_NOISE = 1.5      # s: a slash or roll brings the next one this soon
NOISE_PULL = 5.0             # s a loud noise keeps pulling arrivals toward it
SPAWN_MIN_DIST = 240         # px: never right next to the hero
# weight: (hitstop s, shake canvas px, shake s) - 2 frames / 9 frames of stop (play.jolt)
JOLTS = {"light": (0.035, 1.0, 0.10), "heavy": (0.09, 4.0, 0.25)}   # heavy stop 0.15 -> 0.09 (2026-11-19 "멈추는 틈이 더 짧으면")
FLASH_TIME = 0.035           # s a struck infected shows white (2 frames)
DEFENSE_TIME = 60.0          # s from the start of the station defense to the train (small first)
DEFENSE_WAYS = 3             # they come in by this many entrances nearest the station
STATION_PAD = (120, 40, 80)   # the fenced station: this far left, right and up from the exit
STATION_PEOPLE = (("soldier", -90, 10), ("civilian", -10, 40), ("civilian", 30, 30))   # kind, offset from the exit
SHOVE_REACH = 46             # px a shove reaches
MUFFLED_OFFSET = 55          # px a sound heard through a wreck is misplaced by (Zomboid: +-2 tiles)


DEATH_SUMMARY = 2.2          # s the short "how you died" card shows before the area restarts
HUD_PAD = 40                 # world px the HUD bar covers at the top of the screen


class Game:
    def __init__(self):
        self.hero_look = SheetLook(ROOT / f"assets/characters/hero{LOOK_SUFFIX}")
        if DOT_LOOK and (ROOT / f"assets/characters/{HERO_PX}").exists():    # 8-direction PixelLab hero (2026-11-19)
            self.hero_look = DirLook(ROOT / f"assets/characters/{HERO_PX}", self.hero_look)
        self.zombie_look = SheetLook(ROOT / f"assets/characters/infected{LOOK_SUFFIX}")
        self.aim = (None, None)
        self.deaths = 0
        self.vision = VisionCone(BLOCKS, area.sight_blocks)   # wrecks and walls block the light, windows don't
        self.hurt_flash = 0.0               # s left of the red screen edge after the hero is hit
        self.used = set()                   # actions done at least once (their key marks go away)
        self.note_folded = False            # the goal note, folded to a tab by a click on it
        self.note_click = False             # this left press was on the note: no blow on release
        self.senses = True                  # F2: infected senses on/off (compare)
        self.real = True                    # F3: realistic look on/off (compare)
        self.dev = dev_tools.Dev()          # F1 debug boxes, F4 dev settings (kept across restarts)
        infected.Zombie.show_marks = True   # "!" / "?" stay (2026-11-15 "이 부분은 넣어도 될 것 같습니다")
        infected.Zombie.blink_corpse = not self.real
        self.zoom = ZOOM_DEFAULT            # mouse wheel zoom (kept across restarts)
        self.zoom_shown = float(self.zoom)  # eases toward self.zoom (2026-11-16 "부드럽게")
        self.draw_zoom = None               # while drawing: the whole-number zoom the canvas is made for
        self.bag_open = False               # Tab: the bag (inventory)
        bag_screen.reset(self)
        self.look = 0.0
        self.sounds = Sounds()
        # Rendered in Blender (tools/blender/render_area.py): the ground, and a picture per wreck.
        # A real-map area brings its own ground (tools/map/osm_area.py); its buildings are in it.
        area_dir = ROOT / "assets" / AREA_DIR
        ground = GROUND if GROUND is not None and DOT_LOOK else area_dir / "ground.png"
        self.ground_img = pico2d.load_image(str(ground)) if ground.exists() else None
        pictures = {}
        for look in set(BLOCK_LOOKS):                      # the area's own (furniture), then the shared (wrecks)
            for folder in (area.AREA_PATH, area_dir):
                if folder is not None and (folder / f"{look}.png").exists():
                    pictures[look] = pico2d.load_image(str(folder / f"{look}.png"))
                    break
        self.wreck_imgs = [pictures.get(look) for look in BLOCK_LOOKS]
        self.roofs = [pico2d.load_image(str(area.AREA_PATH / f"{bd['roof']}.png")) for bd in area.BUILDINGS] \
            if DOT_LOOK else []
        # what is drawn standing up: wrecks and furniture (buildings, walls and windows are painted
        # in the ground)
        # in, and the building each stands in (its roof hides it from outside)
        self.standing = [(b[1], "block", (b, img, area.building_at((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)))
                         for b, look, img in zip(BLOCKS, BLOCK_LOOKS, self.wreck_imgs)
                         if look not in ("building", "wall", "window")]
        self.sounds.loop("ai_wind_ruins", 0.35)            # the area's ambience (AI-made, if present)
        fixed = random.Random(4)            # the same cracks every time, without fixing the game's own luck
        self.cracks = [(fixed.uniform(0, ROOM_W), fixed.uniform(0, ROOM_H), fixed.uniform(-1, 1))
                       for _ in range(70)]
        self.reset()

    def reset(self):
        self.hero = Hero(self.hero_look)
        # a start marked "crawler" is one; the others crawl by chance (infected.CRAWLER_SHARE)
        self.zombies = [Zombie(self.zombie_look, s[0], s[1],
                               crawler=s[2] == "crawler" if len(s) > 2 else random.random() < infected.CRAWLER_SHARE)
                        for s in ZOMBIE_STARTS]
        self.effects = []
        # the station (2026-11-18 "역에서 기차가 도착할 때까지 디펜스", "군인, 민간인들이 있다"): people
        # wait by the exit; E there starts the defense, the train comes after DEFENSE_TIME
        ex, ey = (EXIT[0] + EXIT[2]) / 2, EXIT[3] + 30
        self.people = [survivors.place(kind, (ex + dx, ey + dy)) for kind, dx, dy in STATION_PEOPLE]
        self.defense = None          # s left until the train, while the defense runs
        self.station = None
        # the station is fenced off until the hero gets there (2026-11-18 "역에 가니까 이미 다 죽어
        # 있음, 공간을 분리해서 유지되게"): the infected can't step in and don't go for the people
        self.station_zone = (EXIT[0] - STATION_PAD[0], EXIT[1], EXIT[2] + STATION_PAD[1], EXIT[3] + STATION_PAD[2])
        self.station_open = False
        Zombie.keep_out = [self.station_zone]
        # the camera starts on the hero (a real-map area is big: from the corner it slid across it)
        self.cam = [self.hero.x - getattr(self, "view_w", 0) / 2, self.hero.y - getattr(self, "view_h", 0) / 2]
        if hasattr(self, "view_w"):
            self.clamp_camera()
        self.hitstop = self.shake = 0.0
        self.shake_amp, self.shake_len = 0.0, 1.0
        self.slow = False
        self.slow_blend = 0.0
        self.exposure = 0.0
        self.message = ""                  # the keys are taught by marks under the hero (TEACH)
        self.cleared = False
        self.to_spawn = WAVE_TOTAL - len(self.zombies)
        self.director = Director()   # when the infected come in: build up, peak, relax (director.py)
        self.daylight = Daylight()   # the hour: by day the dark outside the cone is lighter (daylight.py)
        self.clock = 0.0
        self.loud = None             # (x, y, time, radius) of the last loud noise
        self.was_slow = False
        self.hero_steps = 0
        self.siren_in = random.uniform(15, 30)
        self.supplies = [Supply(x, y, kind) for x, y, kind in SUPPLIES if EXPOSURE_ON or kind != "pill"]
        self.ground_weapons = [[x, y, name] for x, y, name in WEAPONS_LYING]    # [x, y, weapon key]
        self.condition = Condition()         # tension, wounds (status icons)
        self.death_cause, self.death_time = "", 0.0
        self.stains = []             # blood on the ground (realistic look)
        self.bag_open = False
        bag_screen.reset(self)
        self.message_at = 0.0
        self.bag = {kind: 0 for kind in KINDS}
        self.bag_places = []         # where each thing lies in the bag (bag_grid)
        self.ammo = 0                # rounds for the gun (weapons.py "shot"); found with a gun
        self.kills = 0
        self.left = False            # reached the exit: the area is done

    def mouse_world(self, sx, sy):
        k = self.zoom * DOT                          # screen px per world unit
        return sx / k + self.cam[0], (HEIGHT - 1 - sy) / k + self.cam[1]

    @property
    def canvas_size(self):
        """The world canvas in canvas px: the screen divided by the zoom, rounded up."""
        z = self.draw_zoom or self.zoom
        return -(-WIDTH // z) if DOT_LOOK else round(WIDTH / z), \
            -(-HEIGHT // z) if DOT_LOOK else round(HEIGHT / z)

    @property
    def view_w(self):
        return self.canvas_size[0] / DOT          # world units across the screen at this zoom

    @property
    def view_h(self):
        return self.canvas_size[1] / DOT

    def wheel(self, steps):
        """Mouse wheel: up zooms in, down zooms out, through ZOOM_STEPS; the camera keeps the hero
        in the middle. The picture eases there (zoom_shown, about 0.2 s) and then sits exactly on
        the whole-number zoom, so every pixel is even again (2026-11-16 "휠로 부드럽게")."""
        i = ZOOM_STEPS.index(self.zoom) if self.zoom in ZOOM_STEPS else ZOOM_STEPS.index(ZOOM_DEFAULT)
        i = max(0, min(len(ZOOM_STEPS) - 1, i + (1 if steps > 0 else -1)))
        if ZOOM_STEPS[i] != self.zoom:
            self.zoom = ZOOM_STEPS[i]
            self.cam = [self.hero.x - self.view_w / 2, self.hero.y - self.view_h / 2]
            self.clamp_camera()

    def jolt(self, weight, z=None):
        """How a blow lands, in two weights (2026-11-18 "때려도 시원하지 않다", game-feel research:
        shaking on every hit numbs it, so only the blows that matter shake hard):
        - "light": a hit that does not drop it - 2 frames stop, a 1 px tremble for 0.1 s
        - "heavy": a finishing blow, the head, the legs cut, a countered claw, the hero hit -
          9 frames stop, a 4 px shake both ways for 0.25 s
        The struck infected flashes white for 2 frames either way."""
        stop, amp, length = JOLTS[weight]
        self.hitstop = max(self.hitstop, stop)
        if amp >= self.shake_amp or self.shake <= 0:
            self.shake, self.shake_amp, self.shake_len = length, amp, length
        if z is not None:
            z.flash = FLASH_TIME

    def wound_fx(self, z, zx, zy, sx, sy):
        """A slash that does not drop the infected: a little blood or a spark, a short hitstop."""
        ang = atan2(zy - sy, zx - sx)
        self.sounds.play("slash_hit", 0.8)
        self.effects.append(Blood(zx, zy - 6, ang, 10) if self.real else Spark(zx, zy + 4))
        self.jolt("light", z)

    def right_click(self, sx, sy):
        """Shove: infected right in front reel (or fall) and any attack they wind up is broken off."""
        self.aim = (sx, sy)
        hero = self.hero
        if not hero.start_shove(*self.mouse_world(sx, sy)):
            return
        self.used.add("shove")
        self.sounds.play("roll", 0.5)
        for z in self.zombies:
            if not z.alive or z.prone:                                # nothing to shove on the ground
                continue
            diff = (atan2(z.y - hero.y, z.x - hero.x) - hero.shove_angle + pi) % (2 * pi) - pi
            if hypot(z.x - hero.x, z.y - hero.y) <= SHOVE_REACH and abs(diff) <= 0.9:
                countered = z.shoved(hero.x, hero.y, weak=hero.shove_weak)
                self.sounds.play("slash_hit", 0.6 if countered else 0.35, at=(z.x, z.y))
                if countered:                                  # timed to its swing: a heavier jolt
                    self.jolt("heavy", z)
                    self.effects.append(Spark(z.x, z.y + 40, big=True))      # a flash where it was hit
        if hero.shove_weak:
            hero.stamina.tired_flash = 0.6                     # out of breath: the stamina bar flashes red
        if self.senses:
            self.make_noise(NOISE_STEP)

    def ground_target(self, angle):
        """The crawler the click stomps, or None: the nearest infected toward the aim (on the
        ground, within the stomp's angle) when it is a crawler (2026-11-16 "밟기")."""
        hero, best = self.hero, None
        reach = weapons.attack_range(hero.weapon) + weapons.BODY_MARGIN
        for z in self.zombies:
            if not z.alive:
                continue
            dist = hypot(z.x - hero.x, z.y - hero.y)
            diff = (atan2(z.y - hero.y, z.x - hero.x) - angle + pi) % (2 * pi) - pi
            if dist <= reach and abs(diff) <= weapons.STOMP_ARC and (best is None or dist < best[0]):
                best = (dist, z)
        return best[1] if best is not None and best[1].prone else None

    def aimed(self, sx, sy):
        """What the cursor at screen (sx, sy) aims at (2026-11-16 "커서 방향에 따라 공격 위치가 다르게"):
        (infected, part), or None (the blow goes that way at torso height).
        The path of the blow runs from the hero's chest toward the cursor; the first infected
        body it passes, within reach, is the one it goes for, and the height where it passes
        sets the part - raise the cursor a little to go for the head, lower it for the legs.
        The cursor does not have to be on the infected (2026-11-16 "커서를 안 갖다 대도 가능하게").
        A cursor right on a body picks that body and part."""
        wx, wy = self.mouse_world(sx, sy)
        hero, w = self.hero, self.hero.weapon
        seen = [z for z in self.zombies if z.alive
                and self.vision.visible((hero.x, hero.y), self.look, z.x, z.y)]
        on = [(z, weapons.part_at(z, wx, wy)) for z in seen]
        on = [(z, part) for z, part in on if part]
        if on:
            return min(on, key=lambda h: h[0].y)                    # lower on screen = in front
        sx0, sy0 = hero.x, hero.y + CHEST
        length = hypot(wx - sx0, wy - sy0) or 1
        dx, dy = (wx - sx0) / length, (wy - sy0) / length
        reach = weapons.attack_range(w) + weapons.BODY_MARGIN    # the tip, plus half a body
        best = None
        for z in seen:
            # where the path passes closest to the middle of the body, and at what height
            mid = 6 if z.prone else 27                      # a crawler lies low, a standing body is tall
            mx, my = z.x - sx0, z.y + mid - sy0
            t = mx * dx + my * dy
            if not 0 < t <= reach:
                continue
            px_, py_ = sx0 + dx * t, sy0 + dy * t
            if abs(px_ - z.x) > weapons.PART_HALF_WIDTH * (2.2 if z.prone else 1.5) or abs(py_ - (z.y + mid)) > 40:
                continue
            part = weapons.path_part(z, py_ - z.y)
            if part and (best is None or t < best[0]):
                best = (t, z, part)
        if best:
            return best[1], best[2]
        # Nothing standing on the path: a crawler inside the range and its arc is the one, marked
        # "밟기" (2026-11-16 "밟기 판정이 이상함": aimed at it at chest height it was stomped
        # without a target and the foot hit nothing).
        ang = atan2(wy - hero.y, wx - hero.x)            # on the ground, like ground_target
        crawlers = []
        for z in seen:
            if not z.prone:
                continue
            d = hypot(z.x - hero.x, z.y - hero.y)
            off = abs((atan2(z.y - hero.y, z.x - hero.x) - ang + pi) % (2 * pi) - pi)
            if d <= reach and off <= weapons.STOMP_ARC:
                crawlers.append((d, z))
        return (min(crawlers, key=lambda c: c[0])[1], "ground") if crawlers else None

    def press(self, sx, sy):
        """Left button down: raise the weapon and hold it, aiming with the cursor - or, on the goal
        note, fold or open it."""
        l, t, r, b = hud.note_rect(self)
        if l <= sx / px.K <= r and t <= sy / px.K <= b:
            self.note_folded = not self.note_folded
            self.note_click = True
            return
        self.aim = (sx, sy)
        self.hero.start_ready()

    def release(self, sx, sy):
        """Left button up: the blow, at what the cursor aims at."""
        if self.note_click:
            self.note_click = False
            return
        self.click(sx, sy)

    def click(self, sx, sy):
        self.aim = (sx, sy)
        before = self.hero.slash
        aim = self.aimed(sx, sy)
        # the blow goes toward the cursor - exactly where the shown arc is (2026-11-16 "두 검로가
        # 같아야"); the aimed body is still hit, being on that path
        ax, ay = self.mouse_world(sx, sy)
        angle = atan2(ay - (self.hero.y + CHEST), ax - self.hero.x)
        if aim is None:                                  # a crawler toward the aim: the stomp's target
            crawler = self.ground_target(angle)
            aim = (crawler, "ground") if crawler is not None else None
        shot = self.hero.weapon.get("shot")
        if shot and self.ammo <= 0:                      # an empty gun: a click, nothing more
            if self.hero.free:
                self.sounds.play("dry", 0.7)
                self.hero.slash_cooldown = 0.2
            self.hero.ready = None
            return
        stomp = aim is not None and aim[0].prone and not shot      # a gun is fired at a crawler too
        if aim is not None and aim[1] in ("head", "legs") and self.hero.charge < 1.0:
            aim = (aim[0], "torso")                      # not charged: the torso, whatever the aim
        self.hero.start_slash(ax, ay, stomp=stomp, aim=aim)
        if self.hero.slash is not None and self.hero.slash is not before:
            self.used.add("attack")
        if self.hero.slash is not None and self.hero.slash is not before:
            self.hero.slash["quiet"] = False
            if not shot:
                self.sounds.play("slash", 0.8)

    def equip(self, key):
        """Take a carried weapon in hand; the one in hand goes into the bag (2026-11-16)."""
        hero = self.hero
        held = weapons.key_of_weapon(hero.weapon)
        if key == held or not self.bag.get(weapons.item(key)):
            return
        if not bag_grid.room_for(self, weapons.item(held), without=weapons.item(key)):
            self.message = "배낭에 자리가 없어 손에 든 무기를 넣을 수 없다"
            return
        self.bag[weapons.item(key)] -= 1
        self.bag[weapons.item(held)] = self.bag.get(weapons.item(held), 0) + 1
        hero.weapon = weapons.WEAPONS[key]
        hero.ready = None
        self.message = f"{supply_rules.with_object_particle(hero.weapon['name'])} 들었다 · {hero.weapon['good']}"
        self.sounds.play("pickup", 0.6)

    def next_weapon(self):
        """Q: the next weapon in the bag into the hand."""
        carried = sorted(k for k, n in self.bag.items() if n and weapons.key_of(k))
        if not carried:
            self.message = "배낭에 다른 무기가 없다"
            return
        self.equip(weapons.key_of(carried[0]))

    def use(self, kind):
        """Use one supply from the bag (keys 1/2 or Enter in the bag); a weapon is taken in hand."""
        if weapons.key_of(kind):
            self.equip(weapons.key_of(kind))
            return
        if self.hero.dead or not self.bag.get(kind):
            return
        if kind == "bandage" and (self.hero.hp < HERO_HP or self.condition.bleeding):
            self.bag[kind] -= 1
            self.used.add("bandage")
            treated = self.condition.treat()
            before = self.hero.hp
            self.hero.hp = min(HERO_HP, self.hero.hp + BANDAGE_HEAL)
            gained = self.hero.hp - before
            self.message = "붕대를 감았다" + (" (피가 멎었다)" if treated else "") +                 (f" 체력 +{gained:.0f}%" if gained >= 1 else "")
            self.sounds.play("pickup", 0.6)
        elif kind == "pill" and EXPOSURE_ON:
            self.bag[kind] -= 1
            self.exposure = max(0.0, self.exposure - PILL_EFFECT)
            self.message = f"피폭 억제제를 먹었다 (피폭 -{PILL_EFFECT:.0f})"
            self.sounds.play("pickup", 0.6)
        elif kind == "can" and self.hero.hp < HERO_HP:
            self.bag[kind] -= 1
            before = self.hero.hp
            self.hero.hp = min(HERO_HP, self.hero.hp + supply_rules.CAN_HEAL)
            self.message = f"통조림을 먹었다 체력 +{self.hero.hp - before:.0f}%"
            self.sounds.play("pickup", 0.6)
        elif kind == "can":
            self.message = "체력이 가득하다"
        elif kind == "bandage":
            self.message = "다친 곳이 없다"

    def key_down(self, key, keys):
        if dev_tools.key(self, key):                       # F1 boxes, F4 dev panel (and its keys)
            return
        if self.bag_open:                                  # the bag takes the keys while it is open
            shift = keys[sdl2.SDL_SCANCODE_LSHIFT] or keys[sdl2.SDL_SCANCODE_RSHIFT]
            bag_screen.key(self, key, bool(shift))
            return
        if key == sdl2.SDLK_TAB and not self.left and not self.hero.dead:
            self.bag_open = True
            self.bag_drag = None
            self.bag_note_from = self.message              # only what happens in the bag is shown there
            self.slow = False
            return
        if key == sdl2.SDLK_q and not self.left and not self.hero.dead:
            self.next_weapon()
            return
        if key == sdl2.SDLK_SPACE:
            rolled = self.hero.start_roll(keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A],
                                          keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S])
            if rolled:
                self.used.add("roll")
                self.sounds.play("roll", 0.6)
        elif key == sdl2.SDLK_r:
            self.reset()
        elif key == sdl2.SDLK_e and not self.left and not self.hero.dead:
            self.interact()
        elif sdl2.SDLK_1 <= key <= sdl2.SDLK_9 and chr(key) in supply_rules.QUICK_KEYS.values():
            self.use(next(k for k, v in supply_rules.QUICK_KEYS.items() if v == chr(key)))
        elif key == sdl2.SDLK_F3:
            self.toggle_real()
        elif key == sdl2.SDLK_F2:
            self.toggle_senses()

    def toggle_real(self):
        self.real = not self.real
        infected.Zombie.blink_corpse = not self.real
        self.message = "사실적 연출 켬: 피, 시체, 어두운 색" if self.real \
            else "사실적 연출 끔: 예전 연출(반달 궤적, 불꽃)"

    def toggle_senses(self):
        self.senses = not self.senses
        self.reset()
        self.message = ("피폭체 감각 켬: 보고 듣고 찾음, 시야 밖 공격은 예고가 짧음" if self.senses
                        else "피폭체 감각 끔: 예전 규칙(300px 안이면 무조건 쫓아옴)")

    def near_exit(self):
        l, b, r, t = EXIT
        return l - 14 <= self.hero.x <= r + 14 and b - 14 <= self.hero.y <= t + 14

    def interact(self):
        """E: leave through the exit, or pick up the nearest supply (rummaging is heard)."""
        if self.near_exit() and self.defense is None:
            self.start_defense()
            return
        near_weapon = self.nearest_weapon()
        if near_weapon is not None and self.hero.free:
            self.take_weapon(near_weapon)
            self.used.add("pick")
            return
        item = supply_rules.nearest(self.supplies, self.hero.x, self.hero.y)
        if item is None or self.hero.pickup > 0 or self.hero.slash or self.hero.roll > 0:
            return
        if not bag_grid.room_for(self, item.kind):
            self.message = "배낭이 무겁다 (Tab에서 X로 버리기)"
            return
        self.hero.pickup = PICKUP_TIME                     # a short crouch to pick it up
        item.taken = True
        self.bag[item.kind] += 1
        self.used.add("pick")
        self.message = f"{supply_rules.with_object_particle(item.name)} 챙겼다" + (f" ({supply_rules.USE_KEYS[item.kind]}로 사용)"
                                                   if item.kind in supply_rules.USE_KEYS else "")
        self.sounds.play("pickup", 0.8)
        if self.senses:
            self.make_noise(supply_rules.PICK_NOISE)

    def nearest_weapon(self):
        hero = self.hero
        near = [w for w in self.ground_weapons if hypot(w[0] - hero.x, w[1] - hero.y) <= supply_rules.PICK_RANGE]
        return min(near, key=lambda w: hypot(w[0] - hero.x, w[1] - hero.y)) if near else None

    def take_weapon(self, lying):
        """E on a weapon on the ground: into the bag if there is room (Enter in the bag or Q takes
        it in hand), otherwise swap it for the one in hand, which is left in its place."""
        hero = self.hero
        key = lying[2]
        self.ammo += weapons.WEAPONS[key].get("shot", {}).get("rounds", 0)   # a gun comes loaded
        hero.pickup = PICKUP_TIME
        self.sounds.play("pickup", 0.8)
        if bag_grid.room_for(self, weapons.item(key)):
            self.ground_weapons.remove(lying)
            self.bag[weapons.item(key)] = self.bag.get(weapons.item(key), 0) + 1
            self.message = f"{supply_rules.with_object_particle(weapons.WEAPONS[key]['name'])} 배낭에 넣었다 · Q로 들기"
            return
        lying[2] = weapons.key_of_weapon(hero.weapon)
        hero.weapon = weapons.WEAPONS[key]
        self.message = f"배낭이 가득 차 {supply_rules.with_object_particle(hero.weapon['name'])} 바꿔 들었다"

    def fire(self, slash, shot):
        """A gun goes off (weapons.py "shot"): one round less, the bullet along the aim to the first
        infected on its line (a wall stops it, a window does not), the flash, and a bang that
        carries far. Returns the infected hit, or None."""
        hero = self.hero
        self.ammo -= 1
        ox, oy = slash["from"]
        ux, uy = cos(slash["angle"]), sin(slash["angle"])
        limit = min(shot["range"], ray_hit(hero.x, hero.y, ux, uy,
                                           area.sight_blocks(hero.x - shot["range"], hero.y - shot["range"],
                                                             hero.x + shot["range"], hero.y + shot["range"])))
        struck, at = None, limit
        for z in self.zombies:
            if not z.alive:
                continue
            for up in ((6,) if z.prone else (8, CHEST, 40)):      # legs, chest, head: any of the body
                dx, dy = z.x - ox, z.y + up - oy
                t = dx * ux + dy * uy
                if 0 < t < at and abs(dx * uy - dy * ux) <= shot["width"]:
                    struck, at = z, t
        self.effects.append(Tracer(ox + ux * 16, oy + uy * 16, ox + ux * at, oy + uy * at))
        self.sounds.play("shot", 1.0)
        self.jolt("light")                               # the gun kicks
        if self.senses:
            self.make_noise(shot["noise"])
        return struck

    def hero_sees(self, zombie):
        """Is the infected inside the hero's view cone? (The small lit circle around the body
        does not count: what comes from the side or behind is still a blind-side attack.)"""
        off = abs((atan2(zombie.y - self.hero.y, zombie.x - self.hero.x) - self.look + pi) % (2 * pi) - pi)
        return off <= CONE_HALF

    def make_noise(self, radius, at=None):
        """A noise of `radius` px at `at` (default: the hero) - heard by the infected inside it."""
        hx, hy = at or (self.hero.x, self.hero.y)
        dev_tools.heard(self, hx, hy, radius)              # F6 rings
        if radius >= NOISE_ROLL and self.defense is None:  # loud: pulls the next arrivals here...
            fresh = self.loud is None or self.clock - self.loud[2] > 0.5
            self.loud = (hx, hy, self.clock, radius)
            if fresh and self.pulled_entrances():         # ...only through entrances inside its ring
                self.director.noise_calls(SPAWN_AFTER_NOISE)
        for z in self.zombies:
            if not z.alive:
                continue
            # Zomboid: a sound heard through a wreck or wall can't be placed exactly - the
            # infected heads for a spot off by up to MUFFLED_OFFSET px (open ground: exact).
            dist = hypot(hx - z.x, hy - z.y)
            if dist > 1 and ray_hit(z.x, z.y, (hx - z.x) / dist, (hy - z.y) / dist,
                                    area.blocks_between(z.x, z.y, hx, hy)) < dist:
                ox, oy = random.uniform(-1, 1) * MUFFLED_OFFSET, random.uniform(-1, 1) * MUFFLED_OFFSET
                z.hear(hx + ox, hy + oy, radius, origin=(hx, hy))
            else:
                z.hear(hx, hy, radius)

    def start_defense(self):
        """At the station: hold out with the people there until the train comes."""
        self.defense = DEFENSE_TIME
        self.station = (self.hero.x, self.hero.y)         # where the infected are drawn to
        self.station_open = True                          # the fence opens: they can get in now
        Zombie.keep_out = []
        self.to_spawn = max(self.to_spawn, 99)            # they keep coming until the train
        self.director.noise_calls(1.0)                    # the first comes at once
        self.message = f"기차 도착까지 {DEFENSE_TIME:.0f}초 · 버텨라"
        self.sounds.play("alert", 0.9)
        self.loud = (self.hero.x, self.hero.y, self.clock, 10 ** 6)   # the whole area hears the station

    def train_arrives(self):
        self.defense = None
        self.left = True
        self.slow = False
        alive = sum(1 for s in self.people if s.alive)
        self.message = f"기차가 왔다 · 함께 탄 사람 {alive}/{len(self.people)} · R 다시"
        self.sounds.play("exit", 0.8)

    def prey_for(self, z):
        """What an infected goes for: the nearest living body - the hero or one of the people
        (2026-11-18). One already on the hero keeps on him while he is in its sight."""
        hero = self.hero
        if z.state in ("chase", "poised", "windup", "strike", "recover") and getattr(z, "prey", hero) is hero:
            return hero
        bodies = [hero] + [s for s in self.people if s.alive and self.station_open]
        return min(bodies, key=lambda b: (b.x - z.x) ** 2 + (b.y - z.y) ** 2)

    def update_people(self, dt):
        if not self.station_open:                          # behind the fence they wait, the soldier holds fire
            return
        for s in self.people:
            happened = s.update(dt, self)
            if not happened:
                continue
            if happened[0] == "rise":                      # a fallen one gets up as an infected
                z = Zombie(self.zombie_look, s.x, s.y)
                z.state, z.seen_time = "chase", infected.SEEN_BEFORE_STRIKE
                self.zombies.append(z)
                self.message = f"쓰러진 {s.name}이 일어났다"
            else:                                          # a soldier's shot
                _, z, hit = happened
                self.effects.append(Tracer(s.x, s.y + CHEST, z.x, z.y + CHEST))
                self.sounds.play("shot", 0.6, at=(s.x, s.y))
                self.make_noise(s.gun["noise"], at=(s.x, s.y))
                if hit and z.alive:
                    if z.hurt(s.x, s.y, survivors.damage_of(s.gun), "torso"):
                        z.kill(z.x - s.x, z.y - s.y)
                        self.kills_by_people = getattr(self, "kills_by_people", 0) + 1

    def pulled_entrances(self):
        """Entrances a recent loud noise reaches (2026-11-18 "디버그와 동일하게": the noise ring on
        F6 is exactly where it calls new infected from; was the whole map). Far enough from the hero."""
        if not self.senses or self.loud is None or self.clock - self.loud[2] > NOISE_PULL:
            return []
        x, y, _, radius = self.loud
        hero = self.hero
        if self.defense is not None:                       # the station calls them in by the nearest ways
            self.loud = (x, y, self.clock, radius)
            ways = sorted((pos for pos, _ in ENTRANCES if hypot(pos[0] - hero.x, pos[1] - hero.y) >= SPAWN_MIN_DIST),
                          key=lambda pos: hypot(pos[0] - x, pos[1] - y))
            return ways[:DEFENSE_WAYS]
        return [pos for pos, _ in ENTRANCES if hypot(pos[0] - x, pos[1] - y) <= radius
                and hypot(pos[0] - hero.x, pos[1] - hero.y) >= SPAWN_MIN_DIST]

    def spawn(self):
        """One more infected: through an entrance a recent loud noise reaches, heading for it; or else
        through one the hero is not looking at, far enough away."""
        hero = self.hero
        pulled = self.pulled_entrances()
        if pulled:
            x, y = random.choice(pulled)
            z = Zombie(self.zombie_look, x, y, crawler=random.random() < infected.CRAWLER_SHARE)
            z.state, z.target, z.memory = "search", (self.loud[0], self.loud[1]), 8.0
            return self.arrive(z)
        far = [pos for pos, _ in ENTRANCES if hypot(pos[0] - hero.x, pos[1] - hero.y) >= SPAWN_MIN_DIST]
        unseen = [pos for pos in far if abs((atan2(pos[1] - hero.y, pos[0] - hero.x) - self.look + pi)
                                            % (2 * pi) - pi) > CONE_HALF]
        choices = unseen or far
        if not choices:
            return False
        x, y = random.choice(choices)
        z = Zombie(self.zombie_look, x, y, crawler=random.random() < infected.CRAWLER_SHARE)
        if self.senses:                                    # wanders in somewhere
            z.state, z.target, z.memory = "search", (random.uniform(200, ROOM_W - 200),
                                                     random.uniform(150, ROOM_H - 150)), 8.0
        return self.arrive(z)

    def arrive(self, z):
        x, y = z.x, z.y
        self.zombies.append(z)
        self.to_spawn -= 1
        self.sounds.play("alert", 0.7, at=(x, y))          # heard coming in, maybe unseen
        return True

    def draw_fence(self, cx, cy):
        """A low metal fence with posts round the station (open side: the exit's own wall). Rails
        and posts are filled bars at least one canvas pixel thick (a 1-unit line falls between
        canvas pixels and vanishes, 2026-11-18)."""
        l, b, r, t = self.station_zone
        px_ = 1 / DOT                                       # one canvas pixel in world units
        rail, post, edge = (150, 154, 156), (104, 108, 112), (40, 42, 46)
        for x0, y0, x1, y1 in ((l, b, l, t), (l, t, r, t), (r, t, r, b)):
            for lift in (4, 11):                            # two rails
                if y0 == y1:
                    pico2d.draw_rectangle(x0 - cx, y0 + lift - cy, x1 - cx, y0 + lift + px_ * 1.5 - cy, *rail, filled=True)
                else:
                    pico2d.draw_rectangle(x0 - cx, min(y0, y1) + lift - cy, x0 + px_ * 1.5 - cx, max(y0, y1) + lift - cy, *rail, filled=True)
            steps = max(1, int(hypot(x1 - x0, y1 - y0) // 18))
            for k in range(steps + 1):                      # posts
                qx, qy = x0 + (x1 - x0) * k / steps, y0 + (y1 - y0) * k / steps
                pico2d.draw_rectangle(qx - px_ * 1.5 - cx, qy - cy, qx + px_ * 1.5 - cx, qy + 14 - cy, *edge, filled=True)
                pico2d.draw_rectangle(qx - px_ * 0.5 - cx, qy - cy, qx + px_ * 0.5 - cx, qy + 13 - cy, *post, filled=True)

    def update(self, real_dt, keys):
        real_dt *= self.dev.speed                          # dev panel: the whole game slower / faster
        if not (self.left or self.bag_open):
            self.daylight.update(real_dt)
        self.vision.fog = self.daylight.fog            # how dim the world looks
        self.vision.reach = self.daylight.reach        # how far the hero sees: longer by day
        dev_tools.age_noises(self, real_dt)
        hero = self.hero
        self.ease_zoom(real_dt)
        if self.left or self.bag_open:                     # summary or bag open: the world waits
            return
        self.clock += real_dt
        if hero.moving:
            self.used.add("move")
        if hero.sneaking:
            self.used.add("sneak")
        if hero.ready is not None and hero.charge >= 1.0:
            self.used.add("charge")
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
        self.hurt_flash = max(0.0, self.hurt_flash - real_dt)
        if self.hitstop > 0:
            self.hitstop -= real_dt
            return
        world_dt = real_dt * (1 + (SLOW_WORLD - 1) * self.slow_blend)
        aim_x = self.mouse_world(*self.aim)[0] if self.aim[0] is not None else None
        if hero.slash and any(z.alive and hypot(z.x - hero.x, z.y - hero.y) <= BODY_CONTACT for z in self.zombies):
            hero.lunge = (0.0, 0.0)           # bodies stop the lunge: no sliding past the one in front
        hero.update(real_dt, keys, aim_x)
        if int(hero.run_distance) != self.hero_steps:
            self.hero_steps = int(hero.run_distance)
            self.sounds.play("step", 0.1 if hero.sneaking else 0.25)
        if self.aim[0] is not None:          # the hero looks toward the mouse
            ax, ay = self.mouse_world(*self.aim)
            self.look = atan2(ay - hero.y, ax - hero.x)    # from the feet, like the light it turns
        else:
            self.look = 0.0 if hero.facing > 0 else pi
        hero.angle = self.look

        if hero.slash and not hero.slash["hit"] and hero.slash["time"] >= hero.slash["hit_at"]:
            hero.slash["hit"] = True
            sx, sy = hero.x, hero.y + CHEST
            shot = hero.slash["weapon"].get("shot")
            struck = self.fire(hero.slash, shot) if shot else None
            if shot:
                pass                                         # the bullet's line is its trail
            elif hero.slash["stomp"]:                    # the foot comes down on it
                self.jolt("light")
            else:
                ox0, oy0 = hero.slash["from"]                  # the trail runs on the shown arc
                self.effects.append(Streak(ox0, oy0, hero.slash["angle"], weapons.attack_range(hero.slash["weapon"]),
                                           hero.slash["arc"]) if self.real else Crescent(sx, sy, hero.slash["angle"]))
                if SpriteFx.on:                              # the drawn trail over the blow
                    a = hero.slash["angle"]
                    reach = weapons.attack_range(hero.slash["weapon"]) * 0.55
                    self.effects.append(SpriteFx("slash", sx + cos(a) * reach, sy + sin(a) * reach, a))
            reach, arc, weapon = hero.slash["reach"], hero.slash["arc"], hero.slash["weapon"]
            aim = hero.slash.get("aim")
            if not shot and not any(z.alive and hypot(z.x - sx, z.y + CHEST - sy) <= reach for z in self.zombies):
                hero.stamina.pay(stamina_rules.MISS)          # swung at nothing: more breath gone
            stomp = hero.slash["stomp"]
            ox, oy = hero.slash["from"]                        # measured from where the blow started
            span = reach + hero.slash["weapon"]["lunge"] + weapons.BODY_MARGIN   # shown tip + half a body
            for z in self.zombies:
                if not z.alive:
                    continue
                if stomp and not (aim is not None and aim[0] is z):
                    continue                                   # a stomp lands on the one it was for
                if not stomp and not shot and z.prone and weapon["style"] not in weapons.REACHES_GROUND:
                    continue                                   # a stab or a swing passes over a crawler
                zx, zy = z.x, z.y + CHEST
                diff = (atan2(zy - oy, zx - ox) - hero.slash["angle"] + pi) % (2 * pi) - pi
                from_start = hypot(zx - ox, zy - oy)
                touching = hypot(zx - sx, zy - sy) <= BODY_CONTACT
                marked = aim is not None and aim[0] is z and from_start <= span + weapons.PART_HALF_WIDTH
                # the one marked when the button was let go is hit (2026-11-16 "어디가 맞을지 뜨면
                #그때는 공격 판정이 들어가게"); others: inside the shown range and its arc
                if (z is struck) if shot else (touching or marked or (from_start <= span and abs(diff) <= arc)):
                    # no sure kills: the weapon's damage range, by the part (weapons.roll_damage)
                    part = aim[1] if aim is not None and aim[0] is z else "torso"
                    part = "ground" if stomp else "torso" if part == "ground" else part
                    damage = weapons.roll_damage(weapon, part)
                    part = "torso" if part == "ground" else part
                    was_crawling = z.prone
                    push = weapon["push"]
                    if SpriteFx.on and not shot:             # the drawn burst where it lands
                        self.effects.append(SpriteFx("hit", zx, zy, atan2(zy - sy, zx - sx)))
                    if not z.hurt(hero.x, hero.y, damage, part, push, weapon.get("stagger", False)):
                        self.wound_fx(z, zx, zy, sx, sy)          # it takes the blow and keeps coming
                        if z.prone and not was_crawling:              # legs cut: it drops - a heavier jolt
                            self.jolt("heavy", z)
                        continue
                    z.kill(zx - sx, zy - sy)
                    if SpriteFx.on and not shot:
                        self.effects.append(SpriteFx("hit_big", zx, zy))
                    self.kills += 1
                    if part == "head":                           # a head blow that ends it: felt
                        self.effects.append(Blood(zx, zy - 4, atan2(zy - sy, zx - sx), 26))
                        self.jolt("heavy", z)
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
                        self.jolt("heavy", z)
                    else:
                        self.effects.append(Spark(zx, zy + 4, big=True))
                        self.jolt("heavy", z)

        if self.senses and not hero.dead:          # the hero's noise: steps, rolls, slashes
            if hero.slash and hero.slash["time"] <= real_dt:
                self.make_noise(NOISE_STEP if hero.slash.get("quiet") else NOISE_SLASH)   # every melee blow sounds alike (2026-11-16 "근접 무기는 큰 차이 없어도")
            elif hero.roll > 0 and hero.roll >= ROLL_TIME - real_dt:
                self.make_noise(NOISE_ROLL)
            elif hero.moving:
                self.make_noise(NOISE_STEP * (0.4 if hero.sneaking else 1.0))   # sneaking is quiet
        for z in self.zombies:
            if self.dev.freeze:                            # dev panel: they stand still
                break
            state, steps = z.state, int(z.walk)
            if self.defense is not None and z.state in ("idle", "search"):   # the station calls them all in
                z.state, z.target, z.memory = "search", self.station, infected.MEMORY
            prey = self.prey_for(z)
            z.prey = prey
            event = z.update(world_dt, prey, self)
            if event == "hit" and prey is not hero:            # one of the people is clawed
                self.sounds.play("hurt", 0.6, at=(prey.x, prey.y))
                self.effects.append(Blood(prey.x, prey.y + 16, atan2(prey.y - z.y, prey.x - z.x), 8))
                if prey.take_blow():
                    self.message = f"{prey.name}이 쓰러졌다"
                    self.director.person_fell()
                event = None
            if z.alive and z.state in ("chase", "search", "poised"):   # they groan as they come
                z.groan_in = getattr(z, "groan_in", random.uniform(0.5, 3.0)) - world_dt
                if z.groan_in <= 0:
                    self.sounds.play(random.choice(("ai_infected_groan_1", "ai_infected_groan_2")), 0.55,
                                     at=(z.x, z.y))
                    z.groan_in = random.uniform(3.0, 7.0)
            if z.state != state:
                if z.state == "chase" and state in ("idle", "alert", "search"):
                    z.spotted = infected.SPOTTED_TIME                         # "!" - it spotted the hero
                    z.rush = infected.RUSH_TIME                               # ... and runs at him
                    self.sounds.play("ai_infected_scream", 0.6, at=(z.x, z.y))
                elif z.state == "windup":
                    self.sounds.play("warn", 0.9, at=(z.x, z.y))
                elif z.state == "alert":
                    self.sounds.play("alert", 0.8, at=(z.x, z.y))
            elif z.alive and int(z.walk) != steps:
                self.sounds.play("infected_step", 0.35, at=(z.x, z.y))
            if event == "hit" and not hero.invulnerable and not hero.dead and not self.dev.god:
                self.sounds.play("hurt", 1.0)
                hero.take_blow()                              # slowed, more with every blow
                self.director.hero_hit()
                _, damage = self.condition.wound()            # a fixed share, and maybe bleeding
                hero.hp = max(0.0, hero.hp - damage)
                self.hurt_flash = 0.25                        # the screen edge flashes red
                hero.hurt = HURT_INVULNERABLE
                others = sum(1 for o in self.zombies if o is not z and o.alive and not o.prone
                             and hypot(o.x - hero.x, o.y - hero.y) <= GRAB_NEAR)       # crawlers cannot hold
                if self.senses and others and hero.hp > 0 and not z.prone:
                    hero.grabbed = GRAB_TIME             # Zomboid's drag-down: two on him hold him
                    hero.slash = None
                    self.sounds.play("grab", 1.0)
                if self.real:
                    self.effects.append(Blood(hero.x, hero.y + 16, atan2(hero.y - z.y, hero.x - z.x), 10))
                    self.jolt("heavy")
                else:
                    self.effects.append(Spark(hero.x, hero.y + 26))
                    self.jolt("heavy")
                if hero.hp <= 0:
                    hero.dead = 0.001
                    self.deaths += 1
                    self.death_cause = "피폭체에게 당했다"
                    self.death_time = self.clock
        bled = self.condition.update(real_dt, hero, self.zombies)
        if bled and not hero.dead and not self.dev.god:                             # bleeding drains health until bandaged
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
        self.update_people(world_dt)
        if self.defense is not None and not hero.dead:
            self.defense -= world_dt
            if self.defense <= 0:
                self.train_arrives()
        defending = self.defense is not None
        if not hero.dead and self.director.update(world_dt, self):   # the director: is it time?
            if self.to_spawn > 0 and not self.dev.no_spawn:
                self.spawn()
        if not self.cleared and not defending and self.to_spawn == 0 and all(not z.alive for z in self.zombies):
            self.cleared = True
            self.message = "구역 정리! R로 다시 해 보기"
        # the camera may go HUD_PAD past the top edge so nothing up there hides under the HUD bar
        for i, (pos, view, room) in enumerate(((hero.x, self.view_w, ROOM_W), (hero.y, self.view_h, ROOM_H + HUD_PAD))):
            target = max(0, min(room - view, pos - view / 2))
            self.cam[i] += (target - self.cam[i]) * min(1.0, real_dt * 8)

    def clamp_camera(self):
        for i, (view, room) in enumerate(((self.view_w, ROOM_W), (self.view_h, ROOM_H + HUD_PAD))):
            self.cam[i] = max(0, min(room - view, self.cam[i]))

    def ease_zoom(self, dt):
        self.zoom_shown += (self.zoom - self.zoom_shown) * min(1.0, dt * 14)
        if abs(self.zoom_shown - self.zoom) < 0.01:
            self.zoom_shown = float(self.zoom)

    def draw(self):
        # While the zoom eases, the canvas is made for the whole-number zoom just below the shown
        # one (it covers more) around the same centre, and the middle of it is stretched to fit.
        easing = DOT_LOOK and self.zoom_shown != self.zoom
        centre = (self.cam[0] + self.view_w / 2, self.cam[1] + self.view_h / 2)
        self.draw_zoom = max(ZOOM_STEPS[0], int(min(self.zoom_shown, self.zoom))) if easing else None
        cam = (centre[0] - self.view_w / 2, centre[1] - self.view_h / 2) if easing else tuple(self.cam)
        self.draw_canvas(cam)
        self.draw_zoom = None
        sdl2.SDL_RenderSetScale(canvas.renderer, 1.0, 1.0)
        sdl2.SDL_SetRenderTarget(canvas.renderer, None)
        canvas.canvas_height = HEIGHT
        if easing:
            z = self.draw_zoom_used
            cw, ch = -(-WIDTH // z), -(-HEIGHT // z)
            sw, sh = WIDTH / self.zoom_shown, HEIGHT / self.zoom_shown
            src = sdl2.SDL_Rect(round((cw - sw) / 2), round((ch - sh) / 2), round(sw), round(sh))
            sdl2.SDL_RenderCopy(canvas.renderer, self.target, src, sdl2.SDL_Rect(0, 0, WIDTH, HEIGHT))
        elif DOT_LOOK:                                      # whole-number blow-up of the pixel canvas
            cw, ch = self.canvas_size
            sdl2.SDL_RenderCopy(canvas.renderer, self.target, None, sdl2.SDL_Rect(0, 0, cw * self.zoom, ch * self.zoom))
        else:
            sdl2.SDL_RenderCopy(canvas.renderer, self.target, None, sdl2.SDL_Rect(0, 0, WIDTH, HEIGHT))
        self.draw_screen()

    def draw_canvas(self, cam):
        """The world on the pixel canvas, seen from `cam` (world units, bottom left)."""
        self.draw_zoom_used = self.draw_zoom or self.zoom
        if getattr(self, "target_zoom", None) != self.draw_zoom_used:     # the world texture at this zoom
            if getattr(self, "target", None) is not None:
                sdl2.SDL_DestroyTexture(self.target)
            self.target = sdl2.SDL_CreateTexture(canvas.renderer, sdl2.SDL_PIXELFORMAT_RGBA8888,
                                                 sdl2.SDL_TEXTUREACCESS_TARGET, *self.canvas_size)
            sdl2.SDL_SetTextureBlendMode(self.target, sdl2.SDL_BLENDMODE_BLEND)
            self.target_zoom = self.draw_zoom_used
        sdl2.SDL_SetRenderTarget(canvas.renderer, self.target)
        sdl2.SDL_SetRenderDrawColor(canvas.renderer, 30, 30, 34, 255)
        sdl2.SDL_RenderClear(canvas.renderer)
        sdl2.SDL_RenderSetScale(canvas.renderer, DOT, DOT)  # world units -> canvas px
        canvas.canvas_height = self.view_h
        ui.world_labels = [] if DOT_LOOK else None
        if self.shake > 0:                                 # both ways, fading out (jolt)
            amp = self.shake_amp / DOT * (self.shake / self.shake_len)   # canvas px -> world units
            cx, cy = cam[0] + random.uniform(-amp, amp), cam[1] + random.uniform(-amp, amp)
        else:
            cx, cy = cam[0], cam[1]
        if self.ground_img is not None:                    # the rendered street
            self.ground_img.draw(ROOM_W / 2 - cx, ROOM_H / 2 - cy, ROOM_W, ROOM_H)
        else:
            self.draw_plain_ground(cx, cy)
        # roofs over the buildings one can go into - except the one the hero is in, whose floor
        # and walls show (2026-11-16 "건물들도 들어갈 수 있게")
        inside = area.building_at(self.hero.x, self.hero.y)
        for i, (bd, img) in enumerate(zip(area.BUILDINGS, self.roofs)):
            if i != inside:
                l, b, r, t = bd["box"]
                img.draw((l + r) / 2 - cx, (b + t) / 2 - cy, r - l, t - b)
        self.draw_area_edges(cx, cy)
        self.draw_world(cx, cy)

    DOT_GAP = 4                    # canvas px between the range's dots (a 2 px dot, a 2 px gap)

    def draw_aim(self, cx, cy):
        """The reach of the weapon toward the cursor, as the arc its blow ends on - always shown,
        faint; while the weapon is held raised it takes the colour of the part it goes for and that
        part is marked on the body (2026-11-16 "차징 안 할 때도 범위가 뜨면", "그림처럼 끝부분만").
        Dotted on the canvas."""
        hero = self.hero
        if self.aim[0] is None or hero.dead or self.left or self.bag_open or hero.slash:
            return                                         # while it swings, its trail is the arc
        charge = hero.charge if hero.ready is not None and hero.ready >= weapons.QUICK_PRESS else 0.0
        charged = charge >= 1.0
        w = hero.weapon
        aim = self.aimed(*self.aim) if charged else None
        tx, ty = self.mouse_world(*self.aim)              # toward the cursor
        part = aim[1] if aim is not None else "torso"
        faint = (176, 172, 158)                             # pale, like the slash's trail
        full = {"head": (226, 70, 56), "torso": (196, 170, 92), "legs": (120, 160, 210),
                "ground": (214, 128, 52)}[part]
        colour = full
        sx, sy = hero.x, hero.y + CHEST
        ang = atan2(ty - sy, tx - sx)
        length = weapons.attack_range(w)                   # exactly the range the hit uses
        # Where the blow ends: a dotted arc at the reach, exactly as wide as the hit (2026-11-16
        # "점들처럼"; "점 1, 2, 3개는 예시 - 실제 범위에 알맞게"): dots DOT_GAP canvas px apart from one
        # edge of the hit's arc (±arc) to the other, so the dotted row is the real width and a wider
        # weapon simply has a longer row. Faint until the button is held; then the dots fill with
        # colour from the middle out (the charge).
        half = w["cells"] * weapons.CELL_WORLD / 2         # = length * arc: the hit's half-width there
        count = round(2 * half * DOT / self.DOT_GAP) + 1
        if w.get("shot"):                                  # a gun: a dotted sight line as far as it flies
            count = 0
            ux, uy = cos(ang), sin(ang)
            far = min(length, ray_hit(hero.x, hero.y, ux, uy, area.sight_blocks(
                hero.x - length, hero.y - length, hero.x + length, hero.y + length)))
            tint = full if charged else faint if self.ammo > 0 else (120, 60, 54)
            for d in range(24, int(far), 3 * self.DOT_GAP):
                qx = round((sx + ux * d - cx) * DOT) / DOT
                qy = round((sy + uy * d - cy) * DOT) / DOT
                pico2d.draw_rectangle(qx, qy, qx + 1.99 / DOT, qy + 1.99 / DOT, *tint, filled=True)
        for i in range(count):
            off = (i / (count - 1) * 2 - 1) * half         # across the aim, edge to edge
            middle = abs(off) / half                       # 0 in the middle .. 1 at the ends
            tint = full if charge > 0 and middle <= charge else faint
            a = ang + off / length
            # a 2 x 2 canvas-pixel square on the canvas grid: even, crisp dots at any camera
            qx = round((sx + cos(a) * length - cx) * DOT) / DOT
            qy = round((sy + sin(a) * length - cy) * DOT) / DOT
            pico2d.draw_rectangle(qx, qy, qx + 1.99 / DOT, qy + 1.99 / DOT, *tint, filled=True)
        if aim is not None:                               # the part it goes for, on the body
            z = aim[0]
            if z.prone:                                   # a crawler: all of it, on the ground
                low, high, half = -4, 14, weapons.PART_HALF_WIDTH * 2
            else:
                low, high = next((lo, hi) for p, lo, hi in weapons.PARTS if p == part)
                half = weapons.PART_HALF_WIDTH
            l, r = z.x - half - cx, z.x + half - cx
            b, t = z.y + low - cy, z.y + min(high, 56) - cy
            for (x0, y0, dx, dy) in ((l, t, 1, -1), (r, t, -1, -1), (l, b, 1, 1), (r, b, -1, 1)):
                pico2d.draw_rectangle(min(x0, x0 + 5 * dx), y0 - 1, max(x0, x0 + 5 * dx), y0, *colour, filled=True)
                pico2d.draw_rectangle(x0, min(y0, y0 + 5 * dy), x0 + 1, max(y0, y0 + 5 * dy), *colour, filled=True)
            ui.world_text_center(z.x - cx, z.y + (24 if z.prone else 62) - cy, weapons.PART_NAMES[part], colour, 12)

    # Keys taught by doing (2026-11-16 "설명 글이 안 떠도 유저가 알 수 있게" → B): small key marks over
    # the hero's head (under it they hid the [E] of a thing at the feet), two at a time, each gone once that action has been done. No sentences.
    TEACH = (("move", "[WASD] 이동"), ("attack", "[클릭] 공격"), ("roll", "[Space] 구르기"),
             ("charge", "[누르고 있기] 조준"), ("sneak", "[Ctrl] 살금"))

    def key_mark(self, x, y, name):
        """Over a thing E picks up: "[E]" until something has been picked up once, then its name."""
        ui.world_text_center(x, y, name if "pick" in self.used else "[E]", (240, 230, 190), 12)

    def marks_now(self):
        """Key marks for what is happening right now (2026-11-16 C "결과를 글 대신 화면으로"): they
        replace the tip lines. Held by two: [Space] for as long as it lasts; one about to claw within
        reach: [우클릭] until a shove has been tried; bleeding with a bandage: [1] until one is used."""
        hero, marks = self.hero, []
        if hero.grabbed > 0:
            marks.append("[Space] 빠져나가기")
        if "shove" not in self.used and any(
                z.alive and z.state == "windup" and hypot(z.x - hero.x, z.y - hero.y) <= SHOVE_REACH * 2
                for z in self.zombies):
            marks.append("[우클릭] 밀치기")
        if "bandage" not in self.used and self.condition.bleeding and self.bag.get("bandage", 0) > 0:
            marks.append("[1] 붕대")
        return marks

    def draw_teach(self, cx, cy):
        if self.left or self.hero.dead or self.near_exit() or self.bag_open:   # the exit's [E] / the bag covers it
            return
        left = self.marks_now() + [text for action, text in self.TEACH if action not in self.used]
        for i, text in enumerate(left[:2]):
            ui.world_text_center(self.hero.x - cx, self.hero.y - cy + 76 + i * 13, text, (214, 208, 190), 12)   # over the head

    def draw_world_labels(self):
        """Words placed in the world, written crisp on the screen in the pixel font."""
        labels, ui.world_labels = ui.world_labels or [], None
        k = self.zoom * DOT                               # screen px per world unit
        for x, y, value, colour in labels:
            px.text(x * k / px.K, (HEIGHT - y * k) / px.K - 6, value, colour, anchor="m")

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
        if not self.station_open:                          # the station's fence, until the defense
            self.draw_fence(cx, cy)
        near_weapon = self.nearest_weapon()
        for w in self.ground_weapons:                       # weapons lying flat on the ground
            x, y, name = w
            if DOT_LOOK:
                img = weapons.image(weapons.WEAPONS[name]["sprite"])
                img.draw(x - cx, y - cy, img.w / DOT, img.h / DOT)
            if w is near_weapon and not self.near_exit():
                self.key_mark(x - cx, y - cy - 12, weapons.WEAPONS[name]["name"])
        near_item = supply_rules.nearest(self.supplies, self.hero.x, self.hero.y) if near_weapon is None else None
        for s in self.supplies:
            if not s.taken:
                s.draw(cx, cy)
                if s is near_item and not self.near_exit():
                    self.key_mark(s.x - cx, s.y - cy - 12, s.name)
        # sort everything on the ground by depth: lower on screen = nearer = drawn later
        things = list(self.standing)
        things += [(z.y, "z", z) for z in self.zombies]
        things += [(s.y, "s", s) for s in self.people]
        things.append((self.hero.y, "hero", self.hero))
        eye = (self.hero.x, self.hero.y)                  # on the ground
        inside = area.building_at(*eye)
        for _, kind, obj in sorted(things, key=lambda t: -t[0]):
            if kind == "s":
                obj.draw(self.hero_look, cx, cy)
                continue
            if kind == "z" and not self.vision.visible(eye, self.look, obj.x, obj.y):
                continue                                   # out of sight: not drawn at all
            if kind == "z" and area.BUILDINGS and area.building_at(obj.x, obj.y) not in (None, inside):
                continue                                   # inside a house, under its roof
            if kind == "block" and obj[2] is not None and obj[2] != inside:
                continue                                   # furniture under a roof seen from outside
            if kind == "block" and obj[1] is not None:
                (l, b, r, t), img, _ = obj                         # rendered wreck or furniture
                w, h = img.w / DOT, img.h / DOT                    # its pixels are canvas px
                # its bottom on the rect's bottom (2026-11-18: was 3 lower, so a wreck seen from
                # above sat off its own collision rect); tall furniture rises above its footprint
                img.draw((l + r) / 2 - cx, b + h / 2 - cy, w, h)
            elif kind == "block":
                l, b, r, t = obj[0]
                pico2d.draw_rectangle(l - cx, b - cy, r - cx, t + 18 - cy, 44, 38, 36, filled=True)
                pico2d.draw_rectangle(l - cx, t - cy, r - cx, t + 18 - cy, 70, 60, 54, filled=True)
                pico2d.draw_line(l - cx, t + 18 - cy, r - cx, t + 18 - cy, 140, 120, 96)
            else:
                obj.draw(cx, cy)
        for e in self.effects:
            e.draw(cx, cy)
        self.draw_aim(cx, cy)
        # drawn from the feet, where it is worked out (2026-11-18 "장애물 뒤 그림자 인식이 이상": drawn from
        # the chest, every shadow sat CHEST units above where it is - behind a car looked lit)
        self.vision.draw((self.hero.x, self.hero.y), self.look, (self.hero.x - cx, self.hero.y - cy),
                         self.view_w, self.view_h)
        if self.real:                                      # a muted, colder tone over everything
            pico2d.draw_rectangle(0, 0, self.view_w, self.view_h, 26, 30, 34, 70, filled=True)
        night = 1.0 - self.daylight.light                  # night: a cold blue over the world
        if night > 0:
            r, g, b, a = daylight_rules.NIGHT_TINT
            pico2d.draw_rectangle(0, 0, self.view_w, self.view_h, r, g, b, round(a * night), filled=True)
        el, eb, er, _ = EXIT                               # the green exit sign (in front) stays lit in the dark
        ex, ey = (el + er) / 2 - cx, eb - 12 - cy
        pico2d.draw_rectangle(ex - 34, ey - 7, ex + 34, ey + 9, 30, 120, 70, filled=True)
        ui.world_text_center(ex, ey + 1, EXIT_NAME, (220, 255, 225), 11)
        if self.near_exit() and not self.left:
            ui.world_text_center(self.hero.x - cx, self.hero.y - cy + 74, "[E]", (220, 255, 225), 12)
        self.draw_teach(cx, cy)
        dev_tools.draw_sight(self, cx, cy)                  # F5
        dev_tools.draw_sounds(self, cx, cy)                 # F6
        dev_tools.draw_boxes(self, cx, cy)                  # F1
        if self.slow_blend > 0:
            pico2d.draw_rectangle(0, 0, self.view_w, self.view_h, 20, 60, 70, round(80 * self.slow_blend), filled=True)

    def draw_screen(self):
        """Everything drawn on the screen itself over the world canvas."""
        self.draw_world_labels()
        if self.bag_open:                                  # the bag screen replaces the HUD
            hud.draw_inventory(self)
        else:
            hud.draw_stamina(self)
            hud.draw_hud(self)
        if self.left:
            hud.draw_summary(self)
        if self.hero.dead > 0.4:
            hud.draw_death(self)
        dev_tools.draw_director(self)                      # F7
        dev_tools.draw_panel(self)                         # F4
