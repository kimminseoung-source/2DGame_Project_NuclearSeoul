"""Shared tuning for the top-view game (window, hero, slash, infected, exposure).

Numbers came from the side-scroll and top-view prototypes (2026-11-13/14); per-module tuning
(infected senses, the area's wrecks) lives next to the code that uses it.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WIDTH, HEIGHT = 1280, 720       # window (2026-11-15 "화면이 더 크면 좋겠음": was 768 x 432)
# World zoom (2026-11-16 "화면 크기를 키우는 건 좋은데 내부 캐릭터들은 줄이자", "확대 축소가 가능하게
# 하자 휠로"): the mouse wheel steps through these; the default shows the characters smaller than
# before (was a fixed 2.5) and 2.0 keeps every world pixel a whole 2 x 2 block, like the UI.
# The dot look (2026-11-16 "도트 형식으로"): characters are 32 px pixel art (54 world units tall),
# so the world is drawn onto a pixel canvas at DOT canvas px per world unit and the canvas is blown
# up by a whole number - every pixel on screen is the same size (1.5 x / 2.5 x mixed 1- and 2-px
# dots). DOT_LOOK = False brings back the earlier smooth look (zoom steps 1.5-3, no canvas).
DOT_LOOK = os.environ.get("BUSAN_DOT", "1") != "0"   # BUSAN_DOT=0 shows the old look (comparisons)
DOT = 32 / 54 if DOT_LOOK else 1.0          # canvas px per world unit
ZOOM_STEPS = (2, 3, 4) if DOT_LOOK else (1.5, 2.0, 2.5, 3.0)   # screen px per canvas px
ZOOM_DEFAULT = 3 if DOT_LOOK else 2.0
SCALE = ZOOM_DEFAULT * DOT      # starting screen px per world unit (play.Game.zoom changes with the wheel)
LOOK_SUFFIX = "_dot" if DOT_LOOK else ""    # character folders: hero_dot, infected_dot
AREA_DIR = "area/dot" if DOT_LOOK else "area"
# Which area is played: "test" = the first street of wrecks (area.py); any other name = an area in
# assets/areas/<name>, built by tools/map/text_area.py from a hand-made text map (2026-11-16 "골목
# 만들어": "alley", assets/maps/alley.txt) or by tools/map/osm_area.py from a real map ("seoul_station").
AREA = os.environ.get("BUSAN_AREA", "alley")
UI_SCALE = HEIGHT / 432         # HUD text and bars grow with the window

CHEST = 22                      # chest height above the feet, where blows land
# Action tempo (2026-11-16 "모든 행동들이 조금 빠른 감이 있다"): every timed action of the hero and
# the infected - slash, roll, shove, pick-up, being hit, the infected's attack and reactions - lasts
# this many times its base length. Distances stay the same (the roll is slower, not shorter).
TEMPO = 1.3
# The hero's move speed (2026-11-16 "캐릭터 이동속도가 좀비에 비해 빠른 것 같음": was 150, about
# twice a normal infected). Now a normal one (70) is ~2/3 of it and a fast one (98) nearly keeps up,
# so running away works but does not leave them behind at once.
RUN_SPEED = 110.0
ROLL_TIME = 0.28 * TEMPO
ROLL_SPEED = 260.0 * 0.28 / ROLL_TIME     # same 73 px roll
ROLL_COOLDOWN = 0.35
# The slash hits on its impact frame, not at once (was 0.06 s: no wind-up to see), and reaches as
# far as the drawn blade does (tip ~44 px ahead of the body + the infected's half width).
SLASH_TIME = 0.30 * TEMPO       # whole slash
SLASH_HIT = 0.09 * TEMPO        # when the blade connects
SLASH_LUNGE = 34.0              # px travelled along the aim (as before the tempo change)
SLASH_REACH = 58.0              # px from the hero's chest to the infected's (was 58 + 12 slack)
SLASH_ARC = 1.1                 # radians either side of the aim (was 1.25)
SLASH_COOLDOWN = 0.1
# The stomp (2026-11-16 "기어 다니는 거는 발로 밟는 동작으로", was the overhead chop): a click aimed at
# a crawling infected becomes a stamp of the foot (stomp sheet: knee up, lean in, foot down).
STOMP_TIME = 0.45 * TEMPO
STOMP_HIT = 0.24 * TEMPO
STOMP_LUNGE = 12.0
HERO_HP = 100.0                 # health in percent (2026-11-16 "퍼센트로": was 2 hits)
# Being hit (2026-11-16 "맞았을 때 깜박거리는데 수정 필요"): the hero reels a moment (hurt sheet,
# no control) instead of blinking, and stays safe from a second blow a shorter while (was 0.8 s).
HURT_REACT = 0.22 * TEMPO
HURT_INVULNERABLE = 0.5
SLOW_WORLD = 0.12               # world speed while time crawls (right button)
# Exposure (time crawls on the right button, pillar 2) is put off for later (2026-11-15 "피폭 관련된
#거는 추후에 개발"): the code stays, switched off here.
EXPOSURE_ON = False
EXPOSURE_RISE = 16.0            # per real second while time crawls
EXPOSURE_FALL = 3.0
ZOMBIE_SPEED = 70.0
ZOMBIE_REACH = 30.0
ZOMBIE_WINDUP = 0.5 * TEMPO
ZOMBIE_STRIKE = 0.15 * TEMPO
ZOMBIE_RECOVER = 0.6 * TEMPO
ZOMBIE_ARC = 1.0                # radians either side of where it lunged: step around it to dodge

# Legs as a target, crawling infected and the stomp (2026-11-20, "다리는 비활성화, 머리랑 몸통 정도만,
# 2D이다 보니까"): off. Blows find only head and torso, no infected crawls. The code stays; True
# brings it back (docs/plans/2026-11-20_다리_기어다니기_끄기.md).
LEGS_AND_CRAWLERS = False
