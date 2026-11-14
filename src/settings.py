"""Shared tuning for the top-view game (window, hero, slash, infected, exposure).

Numbers came from the side-scroll and top-view prototypes (2026-11-13/14); per-module tuning
(infected senses, the area's wrecks) lives next to the code that uses it.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WIDTH, HEIGHT = 768, 432        # window
SCALE = 1.5                     # the world is drawn zoomed in, so the pixels read chunky
VIEW_W, VIEW_H = round(WIDTH / SCALE), round(HEIGHT / SCALE)   # 512 x 288 world px on screen

CHEST = 22                      # chest height above the feet, where blows land
RUN_SPEED = 150.0
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
SLOW_WORLD = 0.12               # world speed while time crawls (right button)
EXPOSURE_RISE = 16.0            # per real second while time crawls
EXPOSURE_FALL = 3.0
ZOMBIE_SPEED = 70.0
ZOMBIE_REACH = 30.0
ZOMBIE_WINDUP = 0.5
ZOMBIE_STRIKE = 0.15
ZOMBIE_RECOVER = 0.6
