"""Ranged spitters mixed into the alley only (2026-11-26, docs/plans/2026-11-26_원거리피폭체_섞기.md).
Many seeded alley runs: at most SPIT_MAX, none before the SPIT_FROM-th arrival, never two up at once,
never during the defense. The ranged tell's line starts where SpitShot starts and ends at the locked aim."""
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
os.chdir(ROOT)
import pico2d
import sdl2
from pico2d import pico2d as p2

create = p2.SDL_CreateWindow
p2.SDL_CreateWindow = lambda t, x, y, w, h, f: create(t, x, y, w, h, (f | sdl2.SDL_WINDOW_HIDDEN) & ~sdl2.SDL_WINDOW_SHOWN)
from settings import WIDTH, HEIGHT
pico2d.open_canvas(WIDTH, HEIGHT, sync=False)
import attack_tells
import play
from spitter import SpitShot, Spitter

fails = []
game = play.Game()
totals, ever = [], 0
for seed in range(60):
    random.seed(seed)
    game.reset()
    starts = len(game.zombies)
    if any(getattr(z, 'ranged', False) for z in game.zombies):
        fails.append(f'seed {seed}: a starting infected is ranged')
    n = 0
    while game.to_spawn > 0:
        before = sum(z.alive and getattr(z, 'ranged', False) for z in game.zombies)
        if not game.spawn():
            break
        n += 1
        z = game.zombies[-1]
        if getattr(z, 'ranged', False):
            if n < play.SPIT_FROM:
                fails.append(f'seed {seed}: ranged at arrival {n}')
            if before:
                fails.append(f'seed {seed}: two ranged up at once')
            if seed % 2:                       # half the runs: kill it, so the next may come
                z.state = 'dead'
    made = sum(getattr(z, 'ranged', False) for z in game.zombies)
    if made > play.SPIT_MAX:
        fails.append(f'seed {seed}: {made} ranged')
    totals.append(made)

# the defense: no spitter, however many arrive
random.seed(1)
game.reset()
game.start_defense()
for _ in range(80):
    game.spawn()
if any(getattr(z, 'ranged', False) for z in game.zombies[len(game.zombies) - 80:]):
    fails.append('defense spawned a ranged infected')

# tell path == shot path
s = Spitter(game.spitter_look, 300., 200.)
s.facing, s.aim, s.state, s.timer, s.windup = -1, (120., 260.), 'windup', .4, .8
(sx, sy), aim = attack_tells.spit_path(s)
shot = SpitShot(s, s.aim)
if (round(sx, 3), round(sy, 3)) != (round(shot.x, 3), round(shot.y, 3)) or aim != s.aim:
    fails.append(f'tell start {(sx, sy)} vs shot {(shot.x, shot.y)}')
game.zombies = [s]
game.draw()                                   # the tell draws without errors
pico2d.close_canvas()

print(f'alley runs 60: ranged per run min {min(totals)} max {max(totals)} mean {sum(totals)/len(totals):.2f}')
print('FAIL' if fails else 'PASS', *fails[:10], sep='\n')
sys.exit(1 if fails else 0)
