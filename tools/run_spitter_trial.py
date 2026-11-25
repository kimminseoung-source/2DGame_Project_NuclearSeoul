"""Run the isolated ranged-infected trial using the existing hero and controls.

From project root: .venv/Scripts/python.exe tools/run_spitter_trial.py
R restarts, F4 freezes/unfreezes; no default stage or hero assets are replaced.
"""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ['BUSAN_AREA'] = 'arena'
sys.path.insert(0, str(ROOT / 'src'))

from infected import Zombie
from play import Game
from spitter import Spitter, SpitterLook


class SpitterTrial(Game):
    def __init__(self):
        self.spitter_look = SpitterLook()
        super().__init__()

    def reset(self):
        super().reset()
        self.dev.freeze, self.dev.no_spawn = False, True
        self.to_spawn = 0
        self.zombies = [Spitter(self.spitter_look, self.hero.x + 125, self.hero.y),
                        Zombie(self.zombie_look, self.hero.x + 210, self.hero.y + 90)]
        for z in self.zombies:
            z.heading, z.facing = 3.14159265, -1
        self.ground_weapons = []
        self.look = 0.
        self.message = '원거리 피폭체 시험 · R 다시 시작'


if __name__ == '__main__':
    import main
    main.Game = SpitterTrial
    main.main()
