"""Playable red-jacket trial. Distance-driven walk and contact-timed three-key sword cut.
Run from any cwd. --spitter selects the ranged enemy arena instead of the normal stage.
"""
from pathlib import Path
from math import hypot
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import pico2d

if '--spitter' in sys.argv:
    from run_spitter_trial import SpitterTrial as BaseGame
else:
    from play import Game as BaseGame

ART = ROOT / 'assets/characters/previews/hero_redjacket_motion_v1'


class RedJacketLook:
    """Keep the old animation's mechanical timing; replace only its visible drawing."""
    FRAME_TIME = .13
    keys = {}

    def __init__(self, base):
        self.base = base
        names = ('idle', 'guard', 'windup', 'impact', 'recover') + tuple(f'walk_{i}' for i in range(6))
        self.images = {name: pico2d.load_image(str(ART / f'{name}.png')) for name in names}
        self.travel_world = 0.
        self.last_key = 'idle'

    def __getattr__(self, name):
        return getattr(self.base, name)

    def has(self, pose):
        return pose.startswith('ready_') or pose in ('idle', 'run', 'walk')

    def has_dir(self, pose, angle):
        return False       # no authored roll frames: use the existing dodge afterimages

    def blade_lines(self, *args, **kwargs):
        return None        # old hand/blade coordinates do not describe the new artwork

    @staticmethod
    def frame_for(pose, time, contact=None, travel_world=0.):
        walking = pose in ('walk', 'run', 'sneak') or (pose.startswith('ready_') and not pose.startswith('ready_stand_'))
        if walking:
            return f'walk_{int(travel_world / 64 * 6) % 6}'
        if pose in ('chop', 'swing', 'swingh', 'stab'):
            hit = .48 if contact is None else contact
            if time < hit:
                return 'windup'
            after = (time - hit) / max(1e-6, 1 - hit)
            return 'impact' if after < .38 else 'recover'
        if pose.startswith('ready_stand_'):
            return 'windup'
        return 'guard' if pose == 'push' else 'idle'

    def draw(self, pose, time, x, feet_y, facing, contact=None, distance=None,
             alpha=1., held=None, tint=None, angle=None, **kwargs):
        key = self.frame_for(pose, time, contact, self.travel_world)
        self.last_key = key
        im = self.images[key]
        k = 32 / 54
        im.opacify(alpha)
        try:
            im.composite_draw(0, '' if facing > 0 else 'h', x, feet_y + 26/k, 64/k, 64/k)
        finally:
            im.opacify(1.)
        return None


class RedJacketTrial(BaseGame):
    def __init__(self):
        super().__init__()
        self.hero_look = RedJacketLook(self.hero_look)
        self.hero.look = self.hero_look

    def reset(self):
        super().reset()
        self.hero.weapon = dict(self.hero.weapon, name='검 · 외형 시험')
        self.ground_weapons = []  # two review images contain a sword; other weapon art is unfinished
        if isinstance(self.hero_look, RedJacketLook):
            self.hero_look.travel_world = 0.
        self.message = '붉은 재킷 · 걷기/검 베기 1차 · R 다시 시작'

    def update(self, real_dt, keys):
        before = self.hero
        x, y = before.x, before.y
        super().update(real_dt, keys)
        if self.hero is before and self.hero.moving:
            # Count actual displacement, so pushing against a wall does not cycle the feet.
            self.hero_look.travel_world += hypot(self.hero.x - x, self.hero.y - y)


if __name__ == '__main__':
    import main
    main.Game = RedJacketTrial
    main.main()
