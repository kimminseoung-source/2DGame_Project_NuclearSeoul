"""Exploration entry point and game loop."""

from math import hypot
from pathlib import Path
from time import perf_counter

import pico2d
import sdl2
from pico2d import pico2d as canvas

from bat import BAT_DURATION, CRATE_POSITION, BatSwing, draw_crate
from item_ui import draw_filter_icon, draw_filter_slot
from player import DIRECTION_VECTORS, Player
from shelter import SHELTER_EXIT, SHELTER_SPAWN, SHELTER_SUPPLY, ShelterMap
from tile_map import EXIT, HEIGHT, SPAWN, SUPPLY, WIDTH, TileMap


ASSETS = Path(__file__).resolve().parents[1] / "assets"
PICKUP_CROUCH = 0.12
PICKUP_CONTACT = 0.28
PICKUP_STAND = 0.46
PICKUP_DURATION = 0.58
DEFAULT_SPEED = 100
MIN_SPEED = 50
MAX_SPEED = 150
SPEED_STEP = 10


class Exploration:
    def __init__(self):
        self.shelter = ShelterMap(pico2d.load_image(str(ASSETS / "shelter.png")))
        self.player_sprites = {
            action: tuple(
                pico2d.load_image(str(ASSETS / f"survivor_bat_{action}_{group}.png"))
                for group in ("cardinal", "diagonal")
            )
            for action in ("walk", "sneak", "action")
        }
        self.exploration_map = TileMap()
        self.settings_open = False
        self.speed_percent = DEFAULT_SPEED
        reset_world(self)


def near_player(game, point):
    return hypot(game.player.x - point[0], game.player.y - point[1]) <= 34


def interact(game):
    if game.pickup_time is not None or game.bat_swing is not None:
        return
    if not game.has_filter and near_player(game, game.supply):
        game.pickup_time = 0.0
        game.player.start_pickup()
        game.message = "Picking up filter..."
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


def draw_settings(game, font):
    left, bottom = WIDTH // 2 - 176, HEIGHT // 2 - 66
    pico2d.draw_rectangle(left, bottom, left + 352, bottom + 132, 15, 23, 31, filled=True)
    pico2d.draw_rectangle(left, bottom, left + 352, bottom + 132, 135, 170, 157)
    font.draw(left + 22, bottom + 103, "SETTINGS", (181, 197, 209))
    font.draw(left + 22, bottom + 70, f"Movement speed   < {game.speed_percent}% >", (252, 218, 143))
    font.draw(left + 22, bottom + 42, "Left / Right: adjust   R: reset", (181, 197, 209))
    font.draw(left + 22, bottom + 18, "F1 / Esc: resume", (181, 197, 209))


def render_world(game, font):
    pico2d.clear_canvas()
    if game.in_shelter:
        game.tile_map.draw()
    else:
        game.tile_map.draw(game.camera_x)
        crate_x = CRATE_POSITION[0] - game.camera_x
        if -16 < crate_x < WIDTH + 16:
            draw_crate(crate_x, CRATE_POSITION[1], game.crate_broken)
    has_filter, finished, message = game.has_filter, game.finished, game.message
    ex, ey = game.exit
    ex -= game.camera_x
    if -40 < ex < WIDTH + 40:
        if not game.in_shelter:
            pico2d.draw_rectangle(ex - 17, ey - 19, ex + 17, ey + 19, 62, 169, 128, filled=True)
            pico2d.draw_rectangle(ex - 12, ey - 15, ex + 12, ey + 13, 23, 66, 61, filled=True)
        font.draw(ex - 16, ey - 30, "EXIT", (135, 231, 185))
    sx, sy = game.supply
    sx -= game.camera_x
    if not has_filter and -40 < sx < WIDTH + 40:
        draw_filter_icon(sx, sy, scale=2 / 3)
        if game.pickup_time is None and near_player(game, game.supply):
            font.draw(sx - 38, sy + 30, "E  PICK UP", (252, 218, 143))
        else:
            font.draw(sx - 23, sy - 25, "FILTER", (252, 218, 143))

    draw_player(game)
    pico2d.draw_rectangle(0, HEIGHT, WIDTH - 1, HEIGHT + 63, 15, 23, 31, filled=True)
    font.draw(16, HEIGHT + 44, "WASD Move  Shift Sneak  E Use  Space Bat  F1 Settings  Esc Quit", (181, 197, 209))
    font.draw(16, HEIGHT + 18, message, (133, 231, 184) if finished else (245, 222, 169))
    draw_filter_slot(WIDTH - 162, HEIGHT + 8, game.filter_count, font)
    if game.settings_open:
        draw_settings(game, font)
    pico2d.update_canvas()


def draw_player(game):
    player = game.player
    if game.bat_swing is not None:
        player.draw_frame("action", game.bat_swing.frame, game.camera_x)
    elif game.pickup_time is not None and PICKUP_CROUCH <= game.pickup_time < PICKUP_STAND:
        player.draw_frame("action", 0, game.camera_x)
    else:
        player.draw(game.camera_x)


def enter_area(game, in_shelter):
    game.in_shelter = in_shelter
    game.has_filter = False
    game.pickup_time = None
    game.bat_swing = None
    game.crate_broken = False
    game.camera_x = 0
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
    game.player = Player(*spawn, game.tile_map, game.player_sprites)



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
        if event.key == sdl2.SDLK_F1:
            game.settings_open = not game.settings_open
            continue
        if game.settings_open:
            if event.key == sdl2.SDLK_ESCAPE:
                game.settings_open = False
            elif event.key == sdl2.SDLK_LEFT:
                game.speed_percent = max(MIN_SPEED, game.speed_percent - SPEED_STEP)
            elif event.key == sdl2.SDLK_RIGHT:
                game.speed_percent = min(MAX_SPEED, game.speed_percent + SPEED_STEP)
            elif event.key == sdl2.SDLK_r:
                game.speed_percent = DEFAULT_SPEED
            continue
        if event.key == sdl2.SDLK_ESCAPE:
            return False
        if event.key == sdl2.SDLK_e and not game.finished:
            interact(game)
        if event.key == sdl2.SDLK_SPACE and not game.finished:
            if game.pickup_time is None and game.bat_swing is None:
                game.player.walk_time = 0.0
                game.player.direction_release_time = None
                game.bat_swing = BatSwing(DIRECTION_VECTORS[game.player.direction])
        if event.key == sdl2.SDLK_r and game.finished:
            reset_world(game)
    return True


def update_world(game, frame_time):
    if game.settings_open:
        return
    if game.pickup_time is not None:
        previous_time = game.pickup_time
        game.pickup_time += min(frame_time, 0.05)
        if previous_time < PICKUP_CONTACT <= game.pickup_time:
            game.has_filter = True
            game.filter_count += 1
            game.message = "Filter collected. Find the exit."
        if game.pickup_time >= PICKUP_DURATION:
            game.pickup_time = None
    elif game.bat_swing is not None:
        swing = game.bat_swing
        if swing.update(frame_time) and not game.in_shelter and not game.crate_broken:
            if swing.hits(game.player, CRATE_POSITION):
                game.crate_broken = True
                game.message = "Crate broken."
        if swing.elapsed >= BAT_DURATION:
            game.bat_swing = None
    elif not game.finished:
        game.player.update(frame_time, game.speed_percent / 100)
        if not game.in_shelter:
            update_camera(game)


def update_camera(game):
    camera_x = round(game.player.x) - WIDTH // 2
    game.camera_x = max(0, min(camera_x, game.exploration_map.width - WIDTH))


def enlarge_window():
    logical_height = HEIGHT + 64
    display = sdl2.SDL_GetWindowDisplayIndex(canvas.window)
    usable = sdl2.SDL_Rect()
    if display < 0 or sdl2.SDL_GetDisplayUsableBounds(display, usable) != 0:
        return

    scale = min(1.5, (usable.w - 40) / WIDTH, (usable.h - 80) / logical_height)
    if scale <= 1:
        return
    if sdl2.SDL_RenderSetLogicalSize(canvas.renderer, WIDTH, logical_height) != 0:
        return

    window_width = round(WIDTH * scale)
    window_height = round(logical_height * scale)
    sdl2.SDL_SetWindowSize(canvas.window, window_width, window_height)
    sdl2.SDL_SetWindowPosition(
        canvas.window,
        usable.x + (usable.w - window_width) // 2,
        usable.y + (usable.h - window_height) // 2,
    )


def main():
    pico2d.open_canvas(WIDTH, HEIGHT + 64, sync=True)
    try:
        enlarge_window()
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
