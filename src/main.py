"""Exploration entry point and game loop."""

from math import hypot
from pathlib import Path
from time import perf_counter

import pico2d
import sdl2

from player import Player
from shelter import SHELTER_EXIT, SHELTER_SPAWN, SHELTER_SUPPLY, ShelterMap
from tile_map import EXIT, HEIGHT, SPAWN, SUPPLY, WIDTH, TileMap


ASSETS = Path(__file__).resolve().parents[1] / "assets"


class Exploration:
    def __init__(self):
        self.player_image = pico2d.load_image(str(ASSETS / "survivor_walk.png"))
        self.shelter = ShelterMap(pico2d.load_image(str(ASSETS / "shelter.png")))
        self.exploration_map = TileMap()
        reset_world(self)


def near_player(game, point):
    return hypot(game.player.x - point[0], game.player.y - point[1]) <= 34


def interact(game):
    if not game.has_filter and near_player(game, game.supply):
        game.has_filter = True
        game.filter_count += 1
        game.message = "Filter collected. Find the exit."
    elif near_player(game, game.exit):
        if not game.has_filter:
            game.message = "Collect the filter before leaving."
        elif game.in_shelter:
            enter_area(game, in_shelter=False)
        else:
            game.finished = True
            game.message = "Shelter reached! Press R to retry."
    else:
        game.message = "Move closer to the supply or exit."


def render_world(game, font):
    pico2d.clear_canvas()
    game.tile_map.draw()
    has_filter, finished, message = game.has_filter, game.finished, game.message
    ex, ey = game.exit
    if not game.in_shelter:
        pico2d.draw_rectangle(ex - 17, ey - 19, ex + 17, ey + 19, 62, 169, 128, filled=True)
        pico2d.draw_rectangle(ex - 12, ey - 15, ex + 12, ey + 13, 23, 66, 61, filled=True)
    font.draw(ex - 16, ey - 30, "EXIT", (135, 231, 185))
    if not has_filter:
        sx, sy = game.supply
        pico2d.draw_rectangle(sx - 10, sy - 13, sx + 10, sy + 12, 235, 184, 82, filled=True)
        pico2d.draw_rectangle(sx - 8, sy - 4, sx + 8, sy + 3, 76, 57, 37, filled=True)
        font.draw(sx - 23, sy - 25, "FILTER", (252, 218, 143))

    game.player.draw()
    pico2d.draw_rectangle(0, HEIGHT, WIDTH - 1, HEIGHT + 63, 15, 23, 31, filled=True)
    font.draw(16, HEIGHT + 44, "WASD Move   E Interact   Esc Quit", (181, 197, 209))
    font.draw(16, HEIGHT + 18, message, (133, 231, 184) if finished else (245, 222, 169))
    font.draw(WIDTH - 133, HEIGHT + 44, f"Filters: {game.filter_count}", (245, 222, 169))
    pico2d.update_canvas()


def enter_area(game, in_shelter):
    game.in_shelter = in_shelter
    game.has_filter = False
    if in_shelter:
        game.tile_map = game.shelter
        game.supply, game.exit = SHELTER_SUPPLY, SHELTER_EXIT
        spawn = SHELTER_SPAWN
        game.message = "Bunker: collect a filter before heading out."
    else:
        game.tile_map = game.exploration_map
        game.supply, game.exit = SUPPLY, EXIT
        spawn = SPAWN
        game.message = "Outside: collect the spare filter and reach the next shelter."
    game.player = Player(*spawn, game.tile_map, game.player_image)


def reset_world(game):
    game.filter_count = 0
    game.finished = False
    enter_area(game, in_shelter=True)


def handle_events(game):
    for event in pico2d.get_events():
        if event.type == sdl2.SDL_QUIT:
            return False
        if event.type != sdl2.SDL_KEYDOWN:
            continue
        if event.key == sdl2.SDLK_ESCAPE:
            return False
        if event.key == sdl2.SDLK_e and not game.finished:
            interact(game)
        if event.key == sdl2.SDLK_r and game.finished:
            reset_world(game)
    return True


def update_world(game, frame_time):
    if not game.finished:
        game.player.update(frame_time)


def main():
    pico2d.open_canvas(WIDTH, HEIGHT + 64, sync=True)
    try:
        game = Exploration()
        font_path = Path(pico2d.__file__).parent / "data" / "ConsolaMalgun.ttf"
        font = pico2d.load_font(str(font_path), 16)
        previous_time = perf_counter()
        while handle_events(game):
            now = perf_counter()
            update_world(game, now - previous_time)
            previous_time = now
            render_world(game, font)
    finally:
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
