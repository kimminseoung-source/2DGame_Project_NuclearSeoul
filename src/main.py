"""부산까지 entry point, written like the course examples.

open_canvas -> reset_world -> (handle_events -> update_world -> render_world) -> close_canvas.
Every on-screen thing is an object with update()/draw() kept in game_world layers.
This module only holds the play rules that connect objects (pickups, exits, combat start/end).
"""

from ctypes import byref, c_int
from math import hypot
from pathlib import Path
from time import perf_counter

import pico2d
import sdl2
from pico2d import pico2d as canvas

import camera
import game_clock
import game_world
import ui
from background import Background
from character_look import LegacyLook, SheetLook
import hit_feel
import screen_shake
from combat import Combat, Fighter
from combat_view import create_views
from effects import DamageNumber, Impact
from exit_door import ExitDoor
from hud import ExplorationBar, ExplorationHud, InventoryOverlay, SettingsOverlay
from inventory import COLUMNS, Inventory
from player import Player
from shelter import SHELTER_EXIT, SHELTER_SPAWN, ShelterMap
from tile_map import EXIT, HEIGHT, SPAWN, WIDTH, TileMap
from wreck import Wreck
import zombie as zombie_rules
from zombie import Zombie


ASSETS = Path(__file__).resolve().parents[1] / "assets"
# Folder under assets/characters/ with the hero's sheets, or "legacy" for the first hand-drawn hero.
PLAYER_LOOK = "hero"
MAX_HEALTH = 12
DEFAULT_SPEED = 100
MIN_SPEED = 50
MAX_SPEED = 150
SPEED_STEP = 10
SURPRISE_RANGE = 96
# Draft combat stats until characters get full stat sheets.
PLAYER_STATS = dict(
    dexterity=2, move_m=7.5, max_hp=MAX_HEALTH, armor_class=12,
    attack_bonus=4, damage_dice=(1, 6), damage_bonus=2,
)
ZOMBIE_STATS = dict(
    dexterity=0, move_m=6.0, max_hp=9, armor_class=10,
    attack_bonus=3, damage_dice=(1, 6), damage_bonus=0,
)


class Assets:
    """Images and sounds, loaded once after the canvas opens."""

    def __init__(self):
        self.shelter = ShelterMap(pico2d.load_image(str(ASSETS / "shelter_side.png")))
        self.street = TileMap(pico2d.load_image(str(ASSETS / "surface_side.png")))
        if PLAYER_LOOK == "legacy":
            self.player_look = LegacyLook({
                action: pico2d.load_image(str(ASSETS / f"survivor_bat_{action}_side.png"))
                for action in ("walk", "sneak", "action")
            })
        else:
            self.player_look = SheetLook(ASSETS / "characters" / PLAYER_LOOK)
        self.zombie_image = pico2d.load_image(str(ASSETS / "zombie_regular.png"))
        self.wreck_image = pico2d.load_image(str(ASSETS / "street_wreck.png"))
        self.bat_impact_sound = pico2d.load_wav(str(ASSETS / "bat_impact.wav"))
        self.bat_impact_sound.set_volume(65)


class GameState:
    """What survives between areas: health, backpack, settings and the current message."""

    def __init__(self):
        self.max_health = MAX_HEALTH
        self.health = MAX_HEALTH
        self.inventory = Inventory()
        self.inventory_open = False
        self.settings_open = False
        self.settings_row = 0            # 0: walking speed, 1: hit wheel
        self.speed_percent = DEFAULT_SPEED
        self.skip_spin = False           # skip the hit wheel's spin and show the result at once
        self.finished = False
        self.message = ""
        self.in_shelter = True
        self.hitstop = 0.0
        self.aim_x = None


assets = None
state = None
tile_map = None
player = None
zombie = None
exit_door = None
combat = None
exploration_views = []
combat_views = []


# World setup -------------------------------------------------------------------

def reset_world():
    global assets, state
    if assets is None:
        assets = Assets()
    aim_x = state.aim_x if state is not None else None
    speed = state.speed_percent if state is not None else DEFAULT_SPEED
    skip_spin = state.skip_spin if state is not None else False
    state = GameState()
    state.aim_x = aim_x
    state.speed_percent = speed
    state.skip_spin = skip_spin
    enter_area(in_shelter=True)


def enter_area(in_shelter):
    global tile_map, player, zombie, exit_door, combat, exploration_views, combat_views
    game_world.clear()
    camera.reset()
    screen_shake.reset()
    combat, combat_views = None, []
    state.in_shelter = in_shelter
    state.hitstop = 0.0
    tile_map = assets.shelter if in_shelter else assets.street
    spawn, exit_at = (SHELTER_SPAWN, SHELTER_EXIT) if in_shelter else (SPAWN, EXIT)

    player = Player(*spawn, tile_map, assets.player_look)
    exit_door = ExitDoor(*exit_at, in_shelter)
    game_world.add_object(Background(tile_map), game_world.BACKGROUND)
    if tile_map.has_wreck:
        game_world.add_object(Wreck(assets.wreck_image), game_world.GROUND)
    game_world.add_object(player, game_world.GROUND)
    game_world.add_object(exit_door, game_world.EFFECT)
    zombie = None
    if in_shelter:
        state.message = "오른쪽 출입문에서 E를 눌러 지상으로 나가세요."
    else:
        zombie = Zombie(assets.zombie_image, tile_map, player)
        game_world.add_object(zombie, game_world.GROUND)
        state.message = "감염자를 피해 다음 대피소로 이동하세요."
    exploration_views = [
        (ExplorationHud(state), game_world.HUD),
        (ExplorationBar(state, player), game_world.BOTTOM),
    ]
    for view, layer in exploration_views:
        game_world.add_object(view, layer)
    game_world.add_object(InventoryOverlay(state), game_world.POPUP)
    game_world.add_object(SettingsOverlay(state), game_world.POPUP)


# Exploration rules -------------------------------------------------------------

def face_cursor():
    if state.aim_x is None:
        return
    offset = state.aim_x - (player.x - camera.x)
    if abs(offset) > 2:
        player.direction = 1 if offset > 0 else -1


def interact():
    if player.busy():
        return
    if exit_door.near(player):
        if state.in_shelter:
            enter_area(in_shelter=False)
        else:
            state.finished = True
            player.frozen = True
            state.message = "대피소 도착! R로 다시 시작"
    else:
        state.message = "출구에 가까이 가세요."


def can_surprise():
    if zombie is None or zombie.alerted:
        return False
    return hypot(zombie.x - player.x, zombie.y - player.y) <= SURPRISE_RANGE


def attack_click():
    """Left click in real-time play: attack, or queue the combo's next swing.

    A first swing that starts before the infected has noticed the hero is a sneak attack,
    decided now (by the time the blow lands it may have turned around)."""
    if player.state == "SWING":
        player.start_swing()
        return
    if player.busy():
        return
    face_cursor()
    unseen = can_surprise()
    player.start_swing()
    if player.state == "SWING" and unseen:
        player.swing.sneak = True


def handle_player_events():
    for event in player.events:
        if event == "attack_contact" and zombie is not None and zombie.alive:
            position = zombie.x, zombie.y
            if not player.swing.hits(player, position):
                continue
            swing = player.swing.swing
            # Real-time melee: any weapon's swing data decides damage and push. A blow before
            # the infected notices the hero is a sneak attack (the weapon's multiplier).
            sneak = player.swing.sneak
            damage = swing.damage * (player.weapon.sneak_multiplier if sneak else 1)
            zombie.hurt(damage, player.swing.dx, swing.push)
            weight = hit_feel.weight(damage, zombie.max_hp, critical=sneak, finishing=not zombie.alive)
            show_impact(position)
            play_hit_feel(weight)
            game_world.add_object(DamageNumber(zombie.x, zombie.y, damage, weight), game_world.EFFECT)
            if not zombie.alive:
                state.message = "피폭체를 쓰러뜨렸습니다."
            elif sneak:
                state.message = "기습! 큰 피해를 줬습니다."
    player.events.clear()


def handle_zombie_event():
    global zombie
    if zombie is None or combat is not None:
        return
    if zombie.event == "gone":
        game_world.remove_object(zombie)
        zombie = None
        state.message = "길이 열렸습니다. 출구로 이동하세요."
        return
    if zombie.event == "wreck_hit":
        game_world.add_object(Impact(zombie.x, zombie.y), game_world.EFFECT)
        state.message = "폐차에 충돌했습니다. 지금 지나가세요."
    elif zombie.event == "player_hit" and player.invulnerable:
        state.message = "회피!"
    elif zombie.event == "player_hit":
        damage = zombie_rules.DAMAGE
        state.health = max(0, state.health - damage)
        player.take_hit(zombie.direction)
        weight = hit_feel.weight(damage, state.max_health, finishing=state.health == 0)
        play_hit_feel(weight)
        game_world.add_object(DamageNumber(player.x, player.y, damage, weight, ui.PARTY), game_world.EFFECT)
        state.message = "피폭체에게 맞았습니다. \"!\"가 뜨면 Space로 피하세요."
        if state.health == 0:
            state.finished = True
            player.frozen = True
            state.message = "쓰러졌습니다. R로 다시 시작"
    zombie.event = None


def show_impact(position):
    game_world.add_object(Impact(*position), game_world.EFFECT)
    assets.bat_impact_sound.play()


def play_hit_feel(hit_weight):
    """Hit-stop and screen shake for one blow; the same for every attack (see hit_feel.py)."""
    feel = hit_feel.feel(hit_weight)
    state.hitstop = max(state.hitstop, feel.hitstop)
    screen_shake.start(feel.shake, feel.shake_time)


# Combat start and end ----------------------------------------------------------

def start_combat(surprise):
    global combat, combat_views
    player.enter_combat()
    zombie.alerted = True
    zombie.detour = None
    zombie.in_combat = True
    zombie.transition("idle")
    zombie.walk_time = 0.0
    fighters = [
        Fighter(player, "주인공", "party", hp=state.health, **PLAYER_STATS),
        Fighter(zombie, "피폭체", "enemy", **ZOMBIE_STATS),
    ]
    player.direction = 1 if zombie.x > player.x else -1
    zombie.direction = -player.direction
    combat = Combat(camera.x, tile_map, fighters, surprise)
    combat.skip_spin = state.skip_spin
    player.combat = combat
    for view, layer in exploration_views:
        game_world.remove_object(view)
    combat_views = create_views(combat)
    for view, layer in combat_views:
        game_world.add_object(view, layer)
    state.message = "피폭체를 기습했습니다." if surprise else "피폭체에게 발각됐습니다."


def end_combat():
    global combat, combat_views, zombie
    finished_fight = combat
    state.health = next(f.hp for f in finished_fight.fighters if f.unit is player)
    for view, layer in combat_views:
        game_world.remove_object(view)
    combat, combat_views = None, []
    player.combat = None
    player.leave_combat()
    for view, layer in exploration_views:
        game_world.add_object(view, layer)
    if finished_fight.outcome == "defeat":
        state.finished = True
        player.frozen = True
        state.message = "쓰러졌습니다. R로 다시 시작"
    else:
        game_world.remove_object(zombie)
        zombie = None
        state.message = "전투에서 이겼습니다. 출구로 이동하세요."


def handle_combat_results():
    for kind, x, y, hit_weight in combat.effects:
        if kind == "impact":
            show_impact((x, y))
            play_hit_feel(hit_weight)
    combat.effects.clear()
    if combat.finished():
        end_combat()


# Course loop -------------------------------------------------------------------

def handle_events():
    """Read input. Returns False when the game should close."""
    for event in pico2d.get_events():
        if event.type == sdl2.SDL_QUIT:
            return False
        if event.type == sdl2.SDL_MOUSEMOTION:
            state.aim_x = event.x
            if combat is not None:
                region, x, y = ui.split_mouse(event.x, event.y)
                in_world = region == "world"
                combat.hover = (x, y) if in_world else None
                combat.hover_screen = (x, y) if in_world else None
                combat.hover_bottom = None if in_world else (x, y)
        if (event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_RIGHT
                and combat is not None and not state.settings_open):
            combat.right_click()
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_LEFT:
            state.aim_x = event.x
            if state.settings_open:
                pass
            elif combat is not None:
                region, x, y = ui.split_mouse(event.x, event.y)
                if region == "world":
                    combat.click(x, y)
                else:
                    combat.click_bottom(x, y)
            elif not (state.inventory_open or state.settings_open or state.finished):
                # Real-time melee (the turn-based fight is archived): a click attacks, and a
                # click during a swing queues the combo's next swing.
                attack_click()
        if event.type == sdl2.SDL_KEYDOWN and not handle_key(event.key):
            return False
    return True


def handle_key(key):
    # F1 settings work while exploring and in a fight; the game pauses while open.
    if key == sdl2.SDLK_F1 and not state.inventory_open:
        state.settings_open = not state.settings_open
        return True
    if state.settings_open:
        handle_settings_key(key)
        return True
    if combat is not None:
        if key == sdl2.SDLK_ESCAPE:
            return False
        if key == sdl2.SDLK_SPACE and combat.is_player_turn():
            combat.end_turn()
        elif key == sdl2.SDLK_1:
            combat.choose_action("move")
        elif key == sdl2.SDLK_2:
            combat.choose_action("attack")
        elif key == sdl2.SDLK_l:
            combat.toggle_log()
        return True
    if state.inventory_open:
        handle_inventory_key(key)
        return True
    if key == sdl2.SDLK_TAB:
        state.inventory_open = True
        state.inventory.message = ""
    elif key == sdl2.SDLK_ESCAPE:
        return False
    elif key == sdl2.SDLK_e and not state.finished:
        interact()
    elif key == sdl2.SDLK_SPACE and not state.finished and not player.busy():
        face_cursor()
        player.start_dash()
    elif key == sdl2.SDLK_r and state.finished:
        reset_world()
    return True


SETTINGS_ROWS = 2


def handle_settings_key(key):
    """Up/Down pick a row, Left/Right change it, R resets it, Esc closes."""
    if key == sdl2.SDLK_ESCAPE:
        state.settings_open = False
    elif key == sdl2.SDLK_UP:
        state.settings_row = (state.settings_row - 1) % SETTINGS_ROWS
    elif key == sdl2.SDLK_DOWN:
        state.settings_row = (state.settings_row + 1) % SETTINGS_ROWS
    elif state.settings_row == 0:
        if key == sdl2.SDLK_LEFT:
            state.speed_percent = max(MIN_SPEED, state.speed_percent - SPEED_STEP)
        elif key == sdl2.SDLK_RIGHT:
            state.speed_percent = min(MAX_SPEED, state.speed_percent + SPEED_STEP)
        elif key == sdl2.SDLK_r:
            state.speed_percent = DEFAULT_SPEED
    elif key in (sdl2.SDLK_LEFT, sdl2.SDLK_RIGHT):
        state.skip_spin = not state.skip_spin
    elif key == sdl2.SDLK_r:
        state.skip_spin = False
    if combat is not None:
        combat.skip_spin = state.skip_spin


def handle_inventory_key(key):
    if key in (sdl2.SDLK_TAB, sdl2.SDLK_ESCAPE):
        state.inventory_open = False
    elif key == sdl2.SDLK_LEFT:
        state.inventory.select(-1)
    elif key == sdl2.SDLK_RIGHT:
        state.inventory.select(1)
    elif key == sdl2.SDLK_UP:
        state.inventory.select(-COLUMNS)
    elif key == sdl2.SDLK_DOWN:
        state.inventory.select(COLUMNS)
    elif key == sdl2.SDLK_RETURN:
        state.inventory.use_selected()


def update_world(frame_time):
    if state.settings_open or state.inventory_open:
        game_clock.frame_time = 0.0
        return
    # The shake runs on real time, so it keeps going while a hit-stop freezes the scene.
    screen_shake.update(frame_time)
    # A landed blow freezes the scene for a moment (hit-stop), in exploration and in combat.
    frozen = min(state.hitstop, frame_time)
    state.hitstop -= frozen
    frame_time -= frozen
    player.speed_multiplier = state.speed_percent / 100
    if zombie is not None:
        zombie.frozen = state.hitstop > 0
    game_clock.frame_time = max(0.0, frame_time)
    game_world.update()
    if combat is not None:
        handle_combat_results()
        return
    handle_player_events()
    handle_zombie_event()
    if combat is None and not state.in_shelter and player.state != "COMBAT":
        camera.follow(player.x, tile_map.width)
    if combat is None and not player.busy() and not state.finished:
        face_cursor()


def render_world():
    pico2d.clear_canvas()
    game_world.render()
    pico2d.update_canvas()


def enlarge_window():
    logical_height = ui.SCREEN_HEIGHT
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
    pico2d.open_canvas(WIDTH, ui.SCREEN_HEIGHT, sync=True)
    try:
        ui.enable_blending()
        enlarge_window()
        reset_world()
        mouse_x, window_width = c_int(), c_int()
        sdl2.SDL_GetMouseState(byref(mouse_x), None)
        sdl2.SDL_GetWindowSize(canvas.window, byref(window_width), None)
        state.aim_x = mouse_x.value * WIDTH / window_width.value
        face_cursor()
        previous_time = perf_counter()
        while handle_events():
            now = perf_counter()
            update_world(now - previous_time)
            previous_time = now
            render_world()
    finally:
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
