"""Meaningful ranged prototype checks: swept collisions, aim lock, interruption and runtime."""
import ctypes
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
os.environ['BUSAN_AREA'] = 'arena'
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tools')]
import spitter
from spitter import SpitShot, Spitter, WINDUP


class Mechanics(unittest.TestCase):
    def game(self, x=100, y=0, immune=False):
        g = NS(hero=NS(x=x, y=y, dead=False, invulnerable=immune), dev=NS(god=False), hits=0)
        def hit(shot):
            g.hits += 1
        g.spit_hit = hit
        return g

    def shot(self, aim=(100, 0)):
        return SpitShot(NS(x=0., y=0.), aim)

    def test_sweep_hits_without_tunneling(self):
        g = self.game()
        with patch.object(spitter, 'near_blocks', return_value=[]):
            self.assertFalse(self.shot().update(1., g))
        self.assertEqual(g.hits, 1)

    def test_wall_before_hero(self):
        g = self.game()
        with patch.object(spitter, 'near_blocks', return_value=[(50, -10, 51, 10)]):
            self.assertFalse(self.shot().update(1., g))
        self.assertEqual(g.hits, 0)

    def test_inside_wall_and_grazing_wall(self):
        for wall in ((-1, -1, 1, 1), (50, 2, 51, 20)):
            with self.subTest(wall=wall), patch.object(spitter, 'near_blocks', return_value=[wall]):
                g = self.game()
                self.assertFalse(self.shot().update(1., g))
                self.assertEqual(g.hits, 0)

    def test_dodge_consumes_shot(self):
        g = self.game(immune=True)
        with patch.object(spitter, 'near_blocks', return_value=[]):
            self.assertFalse(self.shot().update(1., g))
        self.assertEqual(g.hits, 0)

    def test_moving_sideways_evades_locked_aim(self):
        shot, g = self.shot(), self.game(y=45)
        with patch.object(spitter, 'near_blocks', return_value=[]):
            self.assertTrue(shot.update(1., g))
        self.assertEqual(g.hits, 0)
        self.assertEqual(shot.uy, 0.)

    def test_aim_locks_before_release(self):
        hero = NS(x=125., y=0., dead=False)
        g = NS(hero=hero, senses=True, projectiles=[], hero_sees=lambda z: True)
        z = Spitter(None, 0, 0)
        z.state, z.heading, z.seen_time = 'chase', 0., 1.
        z.update(.01, hero, g)
        self.assertEqual(z.state, 'windup')
        self.assertEqual(z.timer, WINDUP)
        hero.y = 100
        z.update(WINDUP, hero, g)
        self.assertEqual(len(g.projectiles), 1)
        self.assertEqual(g.projectiles[0].uy, 0.)

    def test_torso_hit_interrupts_release(self):
        hero = NS(x=125., y=0., dead=False)
        g = NS(hero=hero, senses=True, projectiles=[], hero_sees=lambda z: True)
        z = Spitter(None, 0, 0)
        z.state, z.timer = 'windup', .1
        z.hurt(125, 0, damage=1)
        z.update(.11, hero, g)
        self.assertEqual(z.state, 'flinch')
        self.assertEqual(g.projectiles, [])


def capture():
    import pico2d, sdl2, ui
    from PIL import Image, ImageDraw, ImageFont
    from pico2d import pico2d as p2
    from run_spitter_trial import SpitterTrial
    from settings import WIDTH, HEIGHT
    create = p2.SDL_CreateWindow
    p2.SDL_CreateWindow = lambda title, x, y, w, h, flags: create(
        title, x, y, w, h, (flags | sdl2.SDL_WINDOW_HIDDEN) & ~sdl2.SDL_WINDOW_SHOWN)
    pico2d.open_canvas(WIDTH, HEIGHT, sync=False)
    out = spitter.ART
    try:
        ui.enable_blending()
        game = SpitterTrial()
        keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
        start_hp = game.hero.hp
        states, shots = set(), False
        for _ in range(150):
            game.update(1/60, keys)
            states.add(game.zombies[0].state)
            shots |= bool(game.projectiles)
        assert game.hero.hp < start_hp, 'projectile must damage the existing hero'
        assert {'windup', 'strike', 'recover'} <= states and shots
        damage_hp = game.hero.hp
        game.reset()
        assert not game.projectiles
        probe = SpitShot(game.zombies[0], (0, 0))
        game.projectiles = [probe]
        pos = (probe.x, probe.y)
        game.bag_open = True
        game.update(.05, keys)
        assert (probe.x, probe.y) == pos, 'bag must pause shots'
        game.bag_open, game.dev.freeze = False, True
        game.update(.05, keys)
        assert (probe.x, probe.y) == pos, 'debug freeze must pause shots'
        game.dev.freeze = False
        game.zombies[0].kill(1, 0)
        game.update(.05, keys)
        assert probe in game.projectiles and (probe.x, probe.y) != pos, 'owner death must not erase shots'
        game.reset()
        game.dev.god = True
        game.used.update(a for a, _ in game.TEACH)
        frames, examples = [], {}
        for tick in range(180):
            game.update(1/60, keys)
            if tick % 6:
                continue
            pico2d.clear_canvas()
            game.draw()
            surf = sdl2.SDL_CreateRGBSurfaceWithFormat(0, WIDTH, HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
            sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888,
                                     surf.contents.pixels, surf.contents.pitch)
            raw = ctypes.string_at(surf.contents.pixels, surf.contents.pitch * HEIGHT)
            im = Image.frombuffer('RGBA', (WIDTH, HEIGHT), raw, 'raw', 'BGRA', surf.contents.pitch, 1).convert('RGB')
            sdl2.SDL_FreeSurface(surf)
            pico2d.update_canvas()
            state = game.zombies[0].state
            if state not in examples:
                examples[state] = im
            frames.append(im.crop((440, 160, 1120, 520)))
        frames[0].save(out / 'game_trial.gif', save_all=True, append_images=frames[1:], duration=100, loop=0)
        examples['windup'].save(out / 'game_trial.png')
        board = Image.new('RGB', (1080, 390), (28, 31, 33))
        draw = ImageDraw.Draw(board)
        font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 18)
        for n, (pose, label) in enumerate((('idle','대기 · 소등'), ('windup','준비 · 점점 발광'),
                                          ('release','발사 · 최대 발광'), ('recover','회복 · 소등'))):
            im = Image.open(out / f'{pose}.png').convert('RGBA')
            if pose in ('windup', 'release'):
                im = Image.alpha_composite(im, Image.open(out / f'{pose}_glow.png').convert('RGBA'))
            im = im.resize((256,256), Image.Resampling.NEAREST)
            board.paste(im, (n*270+7, 50), im)
            draw.text((n*270+26, 24), label, fill=(224,224,210), font=font)
        draw.text((26, 340), '36px 기준 / 준비 0.8초 → 직선 탄 1발 → 회복 1.2초 / 한 방향 시험', fill=(175,188,177), font=font)
        board.save(out / 'attack_board.png')
        result = {'mechanics': '7 checks passed', 'runtime_frames': 330, 'states': sorted(states),
                  'hero_hp_before': start_hp, 'hero_hp_after_150_frames': damage_hp,
                  'reset_clears_projectiles': True, 'capture_uses_existing_hero': True}
        (out / 'runtime_check.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result))
    finally:
        pico2d.close_canvas()


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Mechanics)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    capture()
