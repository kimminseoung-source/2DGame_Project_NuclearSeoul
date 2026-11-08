"""Exploration entry point and game loop."""

from ctypes import byref, c_int
from math import hypot
from pathlib import Path
from time import perf_counter

import pico2d
import sdl2
from pico2d import pico2d as canvas

from bat import (
    BAT_DURATION, BAT_HITSTOP, BAT_IMPACT_TIME, CRATE_POSITION, BatSwing, draw_crate, draw_impact,
)
from inventory import COLUMNS, SPARE_FILTER, Inventory, draw_inventory
from item_ui import draw_filter_icon, draw_filter_slot
from player import Player
from shelter import SHELTER_EXIT, SHELTER_SPAWN, SHELTER_SUPPLY, ShelterMap
from tile_map import EXIT, HEIGHT, SPAWN, SUPPLY, WIDTH, WRECK_LEFT, WRECK_RIGHT, WRECK_Y, TileMap
from zombie import Zombie


ASSETS = Path(__file__).resolve().parents[1] / "assets"
PICKUP_CROUCH = 0.12
PICKUP_CONTACT = 0.28
PICKUP_STAND = 0.46
PICKUP_DURATION = 0.58
MAX_HEALTH = 3
DEFAULT_SPEED = 100
MIN_SPEED = 50
MAX_SPEED = 150
SPEED_STEP = 10


class Exploration:
    def __init__(self):
        self.shelter = ShelterMap(pico2d.load_image(str(ASSETS / "shelter_side.png")))
        self.player_sprites = {
            action: pico2d.load_image(str(ASSETS / f"survivor_bat_{action}_side.png"))
            for action in ("walk", "sneak", "action")
        }
        self.exploration_map = TileMap(pico2d.load_image(str(ASSETS / "surface_side.png")))
        self.zombie_image = pico2d.load_image(str(ASSETS / "zombie_regular.png"))
        self.wreck_image = pico2d.load_image(str(ASSETS / "street_wreck.png"))
        self.bat_impact_sound = pico2d.load_wav(str(ASSETS / "bat_impact.wav"))
        self.bat_impact_sound.set_volume(65)
        self.settings_open = False
        self.aim_x = None
        self.speed_percent = DEFAULT_SPEED
        reset_world(self)


def near_player(game, point):
    return hypot(game.player.x - point[0], game.player.y - point[1]) <= 34


def interact(game):
    if action_in_progress(game):
        return
    if not game.has_filter and near_player(game, game.supply):
        face_cursor(game)
        game.pickup_time = 0.0
        game.player.start_pickup()
        game.message = "필터를 줍는 중…"
    elif near_player(game, game.exit):
        if game.in_shelter and not game.has_filter:
            game.message = "나가기 전에 필터를 챙기세요."
        elif game.in_shelter:
            enter_area(game, in_shelter=False)
        else:
            game.finished = True
            game.message = "대피소 도착! R로 다시 시작"
    else:
        game.message = "물자나 출구에 가까이 가세요."


def draw_settings(game, font):
    left, bottom = WIDTH // 2 - 176, HEIGHT // 2 - 66
    pico2d.draw_rectangle(left, bottom, left + 352, bottom + 132, 15, 23, 31, filled=True)
    pico2d.draw_rectangle(left, bottom, left + 352, bottom + 132, 135, 170, 157)
    font.draw(left + 22, bottom + 103, "설정", (181, 197, 209))
    font.draw(left + 22, bottom + 70, f"이동 속도   < {game.speed_percent}% >", (252, 218, 143))
    font.draw(left + 22, bottom + 42, "좌우 방향키 조절   R 초기화", (181, 197, 209))
    font.draw(left + 22, bottom + 18, "F1 / Esc 계속하기", (181, 197, 209))


def render_world(game, font):
    pico2d.clear_canvas()
    game.tile_map.draw(game.camera_x)
    finished, message = game.finished, game.message
    draw_ground_objects(game, font)
    pico2d.draw_rectangle(0, HEIGHT, WIDTH - 1, HEIGHT + 63, 15, 23, 31, filled=True)
    font.draw(16, HEIGHT + 44, "WASD 이동  Shift 은신  E 상호작용  좌클릭 공격  Space 대시  Tab 배낭  F1", (181, 197, 209))
    font.draw(16, HEIGHT + 18, message, (133, 231, 184) if finished else (245, 222, 169))
    font.draw(500, HEIGHT + 18, f"체력 {game.health}/{MAX_HEALTH}", (238, 169, 149))
    draw_filter_slot(WIDTH - 162, HEIGHT + 8, game.inventory.count(SPARE_FILTER), font)
    if game.settings_open:
        draw_settings(game, font)
    elif game.inventory_open:
        draw_inventory(game.inventory, font, WIDTH, HEIGHT)
    pico2d.update_canvas()


def draw_ground_objects(game, font):
    objects = [(game.player.y, lambda: draw_player(game))]
    if not game.in_shelter:
        crate_x = CRATE_POSITION[0] - game.camera_x
        if -16 < crate_x < WIDTH + 16:
            objects.append((CRATE_POSITION[1], lambda: draw_crate(crate_x, CRATE_POSITION[1], game.crate_broken)))
    if game.zombie is not None:
        objects.append((WRECK_Y, lambda: draw_wreck(game)))
        objects.append((game.zombie.y, lambda: game.zombie.draw(game.camera_x, font)))
    if not game.has_filter:
        objects.append((game.supply[1], lambda: draw_supply(game, font)))
    objects.sort(key=lambda obj: obj[0], reverse=True)
    for _, draw in objects:
        draw()

    if game.bat_impact_time:
        impact_x, impact_y = game.bat_impact_point
        draw_impact(impact_x - game.camera_x, impact_y + 5, game.bat_impact_time)

    ex, ey = game.exit
    ex -= game.camera_x
    if -40 < ex < WIDTH + 40:
        if not game.in_shelter:
            pico2d.draw_rectangle(ex - 16, ey - 12, ex + 16, ey + 40, 46, 105, 92, filled=True)
            pico2d.draw_rectangle(ex - 16, ey - 12, ex + 16, ey + 40, 97, 197, 156)
        font.draw(ex - 16, ey + 48, "출구", (135, 231, 185))


def draw_wreck(game):
    x = (WRECK_LEFT + WRECK_RIGHT) / 2 - game.camera_x
    image = game.wreck_image
    image.draw(x, WRECK_Y - 12 + image.h / 2)


def draw_supply(game, font):
    x, y = game.supply
    x -= game.camera_x
    if not -40 < x < WIDTH + 40:
        return
    draw_filter_icon(x, y, scale=2 / 3)
    if game.pickup_time is None and near_player(game, game.supply):
        font.draw(x - 24, y + 46, "E 줍기", (252, 218, 143))
    else:
        font.draw(x - 15, y + 18 if game.zombie is not None else y - 25, "필터", (252, 218, 143))


def draw_player(game):
    player = game.player
    if game.bat_swing is not None:
        player.draw_frame("action", game.bat_swing.frame, game.camera_x)
        game.bat_swing.draw_trail(player, game.camera_x)
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
    game.bat_hitstop = 0.0
    game.bat_impact_time = 0.0
    game.bat_impact_point = CRATE_POSITION
    game.zombie = None
    game.camera_x = 0
    if in_shelter:
        game.tile_map = game.shelter
        game.supply, game.exit = SHELTER_SUPPLY, SHELTER_EXIT
        spawn = SHELTER_SPAWN
        game.message = "방공호에서 예비 필터를 챙기세요."
    else:
        game.tile_map = game.exploration_map
        game.zombie = Zombie(game.zombie_image, game.tile_map)
        game.supply, game.exit = SUPPLY, EXIT
        spawn = SPAWN
        game.message = "감염자를 피해 다음 대피소로 이동하세요."
    game.player = Player(*spawn, game.tile_map, game.player_sprites)



def reset_world(game):
    game.inventory = Inventory()
    game.health = MAX_HEALTH
    game.inventory_open = False
    game.finished = False
    enter_area(game, in_shelter=True)


def action_in_progress(game):
    return game.pickup_time is not None or game.bat_swing is not None or game.player.dash_time > 0


def face_cursor(game):
    if game.aim_x is None:
        return
    offset = game.aim_x - (game.player.x - game.camera_x)
    if abs(offset) > 2:
        game.player.direction = 1 if offset > 0 else -1


def handle_events(game):
    for event in pico2d.get_events():
        if event.type == sdl2.SDL_QUIT:
            return False
        if event.type == sdl2.SDL_MOUSEMOTION:
            game.aim_x = event.x
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_LEFT:
            game.aim_x = event.x
            if not (game.inventory_open or game.settings_open or game.finished or action_in_progress(game)):
                face_cursor(game)
                game.player.walk_time = 0.0
                game.bat_swing = BatSwing((game.player.direction, 0))
        if event.type != sdl2.SDL_KEYDOWN:
            continue
        if game.inventory_open:
            handle_inventory_key(game, event.key)
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
        if event.key == sdl2.SDLK_TAB:
            game.inventory_open = True
            game.inventory.message = ""
            continue
        if event.key == sdl2.SDLK_ESCAPE:
            return False
        if event.key == sdl2.SDLK_e and not game.finished:
            interact(game)
        if event.key == sdl2.SDLK_SPACE and not game.finished and not action_in_progress(game):
            face_cursor(game)
            game.player.start_dash()
        if event.key == sdl2.SDLK_r and game.finished:
            reset_world(game)
    return True


def handle_inventory_key(game, key):
    if key in (sdl2.SDLK_TAB, sdl2.SDLK_ESCAPE):
        game.inventory_open = False
    elif key == sdl2.SDLK_LEFT:
        game.inventory.select(-1)
    elif key == sdl2.SDLK_RIGHT:
        game.inventory.select(1)
    elif key == sdl2.SDLK_UP:
        game.inventory.select(-COLUMNS)
    elif key == sdl2.SDLK_DOWN:
        game.inventory.select(COLUMNS)
    elif key == sdl2.SDLK_RETURN:
        game.inventory.use_selected()


def update_world(game, frame_time):
    if game.settings_open or game.inventory_open:
        return
    game.bat_impact_time = max(0.0, game.bat_impact_time - frame_time)
    frozen_time = min(game.bat_hitstop, frame_time)
    game.bat_hitstop -= frozen_time
    frame_time -= frozen_time
    if frame_time <= 0:
        return
    game.player.dash_cooldown = max(0.0, game.player.dash_cooldown - frame_time)
    if game.pickup_time is not None:
        previous_time = game.pickup_time
        game.pickup_time += min(frame_time, 0.05)
        if previous_time < PICKUP_CONTACT <= game.pickup_time:
            if game.inventory.add(SPARE_FILTER):
                game.has_filter = True
                game.message = "필터를 주웠습니다. 출구로 이동하세요."
            else:
                game.message = "배낭이 가득 찼습니다. 필터는 바닥에 남아 있습니다."
        if game.pickup_time >= PICKUP_DURATION:
            game.pickup_time = None
    elif game.bat_swing is not None:
        swing = game.bat_swing
        if swing.update(min(frame_time, 0.05)) and game.zombie is not None:
            resolve_bat_contact(game, swing)
        if swing.elapsed >= BAT_DURATION:
            game.bat_swing = None
    elif not game.finished:
        game.player.update(frame_time, game.speed_percent / 100)
        if not game.in_shelter:
            update_camera(game)
        face_cursor(game)

    if game.zombie is not None and not game.finished and not game.bat_hitstop:
        update_zombie(game, min(frame_time, 0.05))


def resolve_bat_contact(game, swing):
    zombie = game.zombie
    position = zombie.x, zombie.y
    if swing.hits(game.player, position):
        if zombie.knock_back(swing.dx):
            show_bat_impact(game, position)
            game.message = "감염자를 밀어냈습니다."
    elif not game.crate_broken and swing.hits(game.player, CRATE_POSITION):
        game.crate_broken = True
        show_bat_impact(game, CRATE_POSITION)
        game.message = "나무 상자를 부쉈습니다."


def show_bat_impact(game, position):
    game.bat_hitstop = BAT_HITSTOP
    game.bat_impact_time = BAT_IMPACT_TIME
    game.bat_impact_point = position
    game.bat_impact_sound.play()


def update_zombie(game, frame_time):
    outcome = game.zombie.update(frame_time, game.player)
    if outcome == "wreck_hit":
        game.bat_impact_point = game.zombie.x, game.zombie.y
        game.bat_impact_time = BAT_IMPACT_TIME
        game.message = "폐차에 충돌했습니다. 지금 지나가세요."
    elif outcome == "player_hit":
        game.health -= 1
        game.player.dash_time = 0.0
        game.pickup_time = None
        game.bat_swing = None
        game.message = "감염자에게 맞았습니다. 거리를 벌리세요."
        if game.health == 0:
            game.finished = True
            game.message = "쓰러졌습니다. R로 다시 시작"


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
        mouse_x, window_width = c_int(), c_int()
        sdl2.SDL_GetMouseState(byref(mouse_x), None)
        sdl2.SDL_GetWindowSize(canvas.window, byref(window_width), None)
        game.aim_x = mouse_x.value * WIDTH / window_width.value
        face_cursor(game)
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
