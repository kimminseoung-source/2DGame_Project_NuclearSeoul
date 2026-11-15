"""Shared tuning for the top-view game (window, hero, slash, infected, exposure).

Numbers came from the side-scroll and top-view prototypes (2026-11-13/14); per-module tuning
(infected senses, the area's wrecks) lives next to the code that uses it.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WIDTH, HEIGHT = 1280, 720       # window (2026-11-15 "화면이 더 크면 좋겠음": was 768 x 432)
# World zoom (2026-11-16 "화면 크기를 키우는 건 좋은데 내부 캐릭터들은 줄이자", "확대 축소가 가능하게
# 하자 휠로"): the mouse wheel steps through these; the default shows the characters smaller than
# before (was a fixed 2.5) and 2.0 keeps every world pixel a whole 2 x 2 block, like the UI.
ZOOM_STEPS = (1.5, 2.0, 2.5, 3.0)
ZOOM_DEFAULT = 2.0
SCALE = ZOOM_DEFAULT            # starting zoom (play.Game.zoom changes with the wheel)
UI_SCALE = HEIGHT / 432         # HUD text and bars grow with the window

CHEST = 22                      # chest height above the feet, where blows land
# Action tempo (2026-11-16 "모든 행동들이 조금 빠른 감이 있다"): every timed action of the hero and
# the infected - slash, roll, shove, pick-up, being hit, the infected's attack and reactions - lasts
# this many times its base length. Distances stay the same (the roll is slower, not shorter).
TEMPO = 1.3
RUN_SPEED = 150.0
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
# The downward chop (2026-11-16 "자동 내려찍기로"): a slash aimed at an infected on the ground
# becomes an overhead chop (swing3 sheet): slower, a short step, the blade lands at its feet.
CHOP_TIME = 0.42 * TEMPO
CHOP_HIT = 0.2 * TEMPO
CHOP_LUNGE = 16.0
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
