"""The infected: senses (sight cone, hearing, memory), the poised hang-back, the alerted turn,
and the warning -> strike -> recover attack. Rules from Project Zomboid's public rules and its
state files and decompiled rules (docs/research/ZOMBOID_REA_ANALYSIS.md parts 1-3); the numbers
are ours. Spotting is a chance, not instant: the nearer, the likelier, and a hero standing still or
sneaking is spotted far less (Zomboid's spot chance)."""

import random
from math import atan2, cos, hypot, pi

import ui
from area import BLOCKS, blocks_between, move_body, waypoint
from settings import TEMPO, ZOMBIE_ARC, ZOMBIE_REACH, ZOMBIE_RECOVER, ZOMBIE_SPEED, ZOMBIE_STRIKE, ZOMBIE_WINDUP
from vision_cone import ray_hit

# Infected senses (numbers are ours; the rules come from Zomboid's sight / hearing / memory).
SIGHT_RANGE = 260               # px an infected sees ahead of it
SIGHT_HALF = 1.1                # radians either side of where it faces
NOTICE_NEAR = 36                # px: so close it notices whatever way it faces
NOISE_STEP = 70                 # px the hero's footsteps carry
NOISE_ROLL = 140
NOISE_SLASH = 230
MEMORY = 8.0                    # s it keeps going to the last place it saw or heard the hero (was 3)
# Spotting (2026-11-18 "특정 거리에서 !가 뜨게, 순간 확률은 헷갈림"; was a chance every moment):
# in its sight (the cone or NOTICE_NEAR, nothing in between) and this close, it spots the hero at
# once ("!"). Farther, never - it only keeps one it has already spotted in sight up to SIGHT_RANGE.
SPOT_DIST = 160                 # px while the hero walks, rolls or swings
SPOT_DIST_QUIET = 90            # px while he stands still or sneaks (Ctrl)
FRONT_SOUND = 0.6               # radians: a sound this close to where it faces needs no turn
WANDER_TURN = (2.0, 5.0)        # s between idle head turns
SPOTTED_TIME = 0.8              # s the "!" stays after it spots the hero
# Heard (2026-11-16 "설명 글 없이도 알 수 있게"): an infected that hears a noise turns its head toward
# it and a "?" pops over it for a moment - the player learns that sound draws them without a line.
HEARD_TIME = 1.0                # s the "?" stays
BLIND_WINDUP = 0.25 * TEMPO     # s of warning when it strikes from outside the hero's sight
SEEN_BEFORE_STRIKE = 0.5        # s it must have seen the hero before it strikes (Zomboid: 0.5)
ALERT_TURN = (0.3, 0.6)         # s it spends turning toward a noise before going
GRAB_TIME = 0.9                 # s the hero is held when a blow lands with another one on him
GRAB_NEAR = ZOMBIE_REACH + 12   # px: "on the hero"
# The shove only pushes it back (2026-11-16 "그냥 살짝 밀쳐내지는 정도로", "밀쳐내기로 가자": a fallen
# infected could not be told from a dead one, so nothing is knocked down any more).
STAGGER_TIME = 0.8 * TEMPO      # s it reels after a shove
SHOVE_PUSH = 130                # px/s it is pushed back (fades 0.88 a frame: about 18 px)
# Toughness (2026-11-16 "좀보이드처럼"): an infected that is facing the hero takes several slashes;
# each one makes it flinch (its attack is broken off). One that is unaware or reeling from a shove
# takes no more than any other (2026-11-16: no sure kills; weapons.py damage ranges).
HEALTH = (8, 12)                # its health; weapons take a range of it off a blow (weapons.py)
CRAWLER_HEALTH = (5, 8)         # one that already crawls is half gone: one or two stomps
FLINCH_TIME = 0.35 * TEMPO      # s it reels from a slash that does not kill it
HIT_PUSH = 55                   # px/s a slash knocks it back
# Reading the infected (2026-11-16 "전투적인 측면을 많이 다듬어야"; sure kills removed later the same day -
# weapons.py damage ranges): after its claw swings it recovers for a moment, and a shove
# timed to the end of its warning is a counter: it reels far back for longer.
COUNTER_WINDOW = 0.22 * TEMPO   # s at the end of the wind-up when a shove is a counter
COUNTER_STAGGER = 1.2 * TEMPO   # s a countered infected reels
COUNTER_PUSH = 290              # px/s it is thrown back (about 40 px)
# Crawlers (2026-11-16 "(나) 처음부터 기어 다니는 피폭체"; Zomboid's zombie-crawler): some infected
# have lost the use of their legs and drag themselves along on the ground - slow
# (the hero stamps on them), biting at the ankles if they are left to reach him.
CRAWLER_SHARE = 0.25            # share of infected that crawl
# Pace (2026-11-16 "좀비별로 이동 속도를 좀 다르게"): each infected walks slow, normal or fast; the
# walk cycle follows the distance, so the legs show it. (share, speed share)
PACES = (("slow", 0.25, 0.7), ("normal", 0.55, 1.0), ("fast", 0.2, 1.4))
CRAWL_SPEED = 0.18              # share of the walking speed (2026-11-16 "속도가 많이 느려지게": was 0.35)
CRAWL_REACH = ZOMBIE_REACH - 6  # px: close enough to bite at the ankles
# The rush (2026-11-16 "좀비가 ! 해서 발견하면 갑자기 달려오면 좋겠음"): the moment it spots the
# hero it breaks into a run for a moment - faster than the hero walks - then settles to its pace.
RUSH_TIME = 1.4                 # s of running after the "!"
RUSH_SPEED = 1.8                # times its own pace (a normal one: 126 px/s, the hero walks 110)


def spot_distance(hero):
    """How close the hero must be, in an infected's sight, to be spotted: nearer when he is quiet."""
    quiet = (hero.sneaking or not hero.moving) and hero.roll <= 0 and not hero.slash
    return SPOT_DIST_QUIET if quiet else SPOT_DIST


class Zombie:
    def __init__(self, look, x, y, crawler=False):
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
        self.spotted = 0.0           # s left of the "!" shown the moment it spots the hero
        self.heard = 0.0             # s left of the "?" shown the moment it hears a noise
        self.rush = 0.0              # s left of the run it breaks into on spotting the hero
        self.seen_time = 0.0         # how long it has kept the hero in sight
        self.turn_from = self.turn_to = 0.0
        self.time = random.random()
        self.walk = 0.0
        self.death = (0.0, 0.0)
        self.push = (0.0, 0.0)
        self.health = random.randint(*(CRAWLER_HEALTH if crawler else HEALTH))
        self.prone = crawler         # a crawler: on the ground, moves and bites from there
        roll, self.pace = random.random(), 1.0
        for name, share, pace in PACES:
            if roll < share:
                self.pace = pace
                break
            roll -= share
        self.on_ground = False       # it was lying down when it died

    @property
    def alive(self):
        return self.state != "dead"

    @property
    def speed(self):
        if self.prone:
            return ZOMBIE_SPEED * CRAWL_SPEED
        rushing = self.rush > 0 and self.state == "chase"
        return ZOMBIE_SPEED * self.pace * (RUSH_SPEED if rushing else 1.0)

    @property
    def reach(self):
        return CRAWL_REACH if self.prone else ZOMBIE_REACH

    def kill(self, dx, dy):
        self.on_ground = self.prone                  # killed lying down: no fall
        self.state, self.timer = "dead", 0.0
        length = hypot(dx, dy) or 1
        self.death = (dx / length * 160, dy / length * 160)

    def reel(self, from_x, from_y, push, state, time):
        """Knocked back from (from_x, from_y) into `state` (stagger or flinch) for `time` s;
        an attack being wound up is broken off."""
        dx, dy = self.x - from_x, self.y - from_y
        length = hypot(dx, dy) or 1
        self.push = (dx / length * push, dy / length * push)
        self.state, self.timer = state, time
        self.seen_time = 0.0
        self.target, self.memory = (from_x, from_y), MEMORY    # it knows where the blow came from

    def shoved(self, from_x, from_y, weak=False):
        """Pushed back by the hero and reeling. A shove right at the end of its warning is a
        counter: it is thrown further and reels longer (a tired, weak shove never is). Returns True
        for a counter."""
        countered = not weak and self.state == "windup" and self.timer <= COUNTER_WINDOW
        if countered:
            self.reel(from_x, from_y, COUNTER_PUSH, "stagger", COUNTER_STAGGER)
        else:
            self.reel(from_x, from_y, SHOVE_PUSH, "stagger", STAGGER_TIME)
        self.stagger_time = self.timer
        return countered

    def hurt(self, from_x, from_y, damage=1, part="torso", push=HIT_PUSH, stagger=False):
        """A blow on an aware infected (weapons.py: damage by the part it lands on): True when it
        was more than it could take. Each part does its own thing (2026-11-16 "다리를 노릴 이유"):
        - legs: always takes them, whatever its health - it crawls from then on
        - torso: the only part that makes it flinch and breaks off its attack
        - head: the most damage, but if it lives it does not even flinch"""
        self.health -= damage
        if self.health <= 0:
            return True
        if part == "legs" and not self.prone:
            self.prone = True                            # crippled: down, dragging itself on
            self.state, self.seen_time = "chase", SEEN_BEFORE_STRIKE
            self.target, self.memory = (from_x, from_y), MEMORY
            return False
        if part == "torso" and stagger:              # a heavy swing: it reels and its attack breaks off
            self.reel(from_x, from_y, push, "stagger", STAGGER_TIME)
            self.stagger_time = self.timer
        elif part == "torso":
            self.reel(from_x, from_y, push, "flinch", FLINCH_TIME)
        return False

    def sees(self, hero):
        """The hero is in its sight: within SIGHT_RANGE in its cone (or NOTICE_NEAR all round), nothing between."""
        dx, dy = hero.x - self.x, hero.y - self.y
        dist = hypot(dx, dy)
        if hero.dead or dist > SIGHT_RANGE:
            return False
        if dist > NOTICE_NEAR:
            off = abs((atan2(dy, dx) - self.heading + pi) % (2 * pi) - pi)
            if off > SIGHT_HALF:
                return False
        return dist < 1 or ray_hit(self.x, self.y, dx / dist, dy / dist,
                                   blocks_between(self.x, self.y, hero.x, hero.y, sight=True)) >= dist

    def hear(self, x, y, radius, origin=None):
        """A noise of `radius` px; (x, y) is where it seems to come from (a muffled sound is
        misplaced), `origin` where it really is - the distance check uses the real spot."""
        ox, oy = origin or (x, y)
        if hypot(ox - self.x, oy - self.y) > radius:
            return
        toward = atan2(y - self.y, x - self.x)
        ahead = abs((toward - self.heading + pi) % (2 * pi) - pi) <= FRONT_SOUND
        if self.state == "idle":
            self.heard = HEARD_TIME                          # "?": it heard that
        if self.state == "idle" and ahead:                   # in front: no need to turn, just go
            self.state, self.target, self.memory = "search", (x, y), MEMORY
        elif self.state == "idle":
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
        way = dist
        if BLOCKS and ray_hit(self.x, self.y, dx / dist, dy / dist, blocks_between(self.x, self.y, x, y)) < dist:
            wx, wy = waypoint(self.x, self.y, x, y)         # something in the way: go around it
            dx, dy = wx - self.x, wy - self.y
            way = hypot(dx, dy)
            if way < 1:
                return dist
        self.heading = atan2(dy, dx)
        if abs(dx) > 1:
            self.facing = 1 if dx > 0 else -1
        step = min(way, self.speed * dt)
        move_body(self, dx / way * step, dy / way * step)
        self.walk += step / 32
        return dist

    def update(self, dt, hero, game):
        self.time += dt
        self.spotted = max(0.0, self.spotted - dt)
        self.heard = max(0.0, self.heard - dt)
        self.rush = max(0.0, self.rush - dt)
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
        elif self.state in ("idle", "alert", "search") and self.sees(hero):
            if dist <= spot_distance(hero):               # close enough in its sight: "!"
                self.state, self.seen_time = "chase", 0.0
                self.target, self.memory = (hero.x, hero.y), MEMORY
        elif self.state in ("chase", "poised"):
            if self.sees(hero):
                self.seen_time += dt
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
            if self.target is None or self.walk_to(*self.target, dt) < 6 or self.memory <= 0:
                self.state, self.turn_in = "idle", 0.6                   # nothing here: give up
        elif self.state in ("chase", "poised"):
            if dist <= self.reach and game.senses and self.seen_time < SEEN_BEFORE_STRIKE:
                self.state = "poised"            # just spotted: hang back, poised (Zomboid 0.5 s)
                self.heading = atan2(dy, dx)
                self.facing = 1 if dx > 0 else -1
            elif dist <= self.reach:
                # From outside the hero's sight the warning is short (Zomboid: from the side
                # and behind they are far more dangerous).
                blind = game.senses and hero is game.hero and not game.hero_sees(self)
                self.windup = BLIND_WINDUP if blind else ZOMBIE_WINDUP
                self.state, self.timer = "windup", self.windup
                self.heading = atan2(dy, dx)
            else:
                self.state = "chase"
                self.walk_to(hero.x, hero.y, dt)
        elif self.state in ("stagger", "flinch"):
            self.timer -= dt
            move_body(self, self.push[0] * dt, self.push[1] * dt)
            self.push = (self.push[0] * 0.88, self.push[1] * 0.88)
            if self.timer <= 0:
                self.state, self.seen_time = "chase", SEEN_BEFORE_STRIKE   # back on it, angry
        elif self.state in ("windup", "strike", "recover"):
            self.timer -= dt
            if self.timer <= 0:
                if self.state == "windup":
                    self.state, self.timer = "strike", ZOMBIE_STRIKE
                    # the claw lands where it lunged: out of reach or around its side, it misses
                    off = abs((atan2(dy, dx) - self.heading + pi) % (2 * pi) - pi)
                    if dist <= self.reach + 8 and off <= ZOMBIE_ARC:
                        event = "hit"
                elif self.state == "strike":
                    self.state, self.timer = "recover", ZOMBIE_RECOVER
                else:
                    self.state = "chase"
        return event

    show_marks = True        # "!" / "?" over the head
    keep_out = []            # rects closed to the infected (area.kept_out; play sets the station's)
    blink_corpse = True      # the corpse blinks; off in the realistic look (bodies stay)

    def draw(self, cx, cy):
        x, y = self.x - cx, self.y - cy
        if self.state == "dead":
            if not self.blink_corpse or self.timer < 1.2 or int(self.timer * 12) % 2 == 0:
                if self.on_ground:                   # already lying there: stays as it lay
                    self.look.draw("down", 1.0, x, y, self.facing)
                else:
                    self.look.draw("down", min(1.0, self.timer * 2), x, y, 1 if self.death[0] < 0 else -1)
        elif self.prone:                                     # a crawler: drags itself, claws from the ground
            moving = self.state in ("chase", "search")
            self.look.draw("crawl", self.time * (1.6 if self.state in ("windup", "strike") else 1.0)
                           if moving or self.state in ("windup", "strike") else 0.0, x, y, self.facing)
            if self.state == "windup" and self.show_marks:
                ui.world_text_center(x, y + 30, "!", (255, 120, 80), 22)
        elif self.state == "windup":
            self.look.draw("attack", 0.25 * (1 - self.timer / self.windup), x, y, self.facing)
            if self.show_marks:
                ui.world_text_center(x, y + 66, "!", (255, 120, 80), 22)
        elif self.state == "strike":
            self.look.draw("attack", 0.45, x, y, self.facing)
        elif self.state == "recover":
            self.look.draw("attack", 0.5 + 0.5 * (1 - self.timer / ZOMBIE_RECOVER), x, y, self.facing)
        elif self.state == "poised":
            self.look.draw("attack", 0.08, x, y, self.facing)        # arms up, not yet striking
        elif self.state in ("stagger", "flinch"):
            whole = getattr(self, "stagger_time", STAGGER_TIME) if self.state == "stagger" else FLINCH_TIME
            self.look.draw("hurt", 1 - self.timer / whole, x, y, self.facing)
        elif self.state in ("chase", "search"):
            self.look.draw("walk", self.time, x, y, self.facing, distance=self.walk)
        else:
            self.look.draw("idle", self.time, x, y, self.facing)
        top = 32 if self.prone else 68
        if self.heard > 0 and self.spotted <= 0 and self.state in ("alert", "search") and self.show_marks:
            pop = 1 + 0.4 * max(0.0, self.heard - HEARD_TIME + 0.15) / 0.15        # pops in, then settles
            ui.world_text_center(x, y + top, "?", (220, 200, 120), round(18 * pop))
        if self.spotted > 0 and self.state not in ("dead", "windup") and self.show_marks:
            pop = 1 + 0.4 * max(0.0, self.spotted - SPOTTED_TIME + 0.15) / 0.15   # pops in, then settles
            ui.world_text_center(x, y + top, "!", (255, 220, 90), round(22 * pop))
