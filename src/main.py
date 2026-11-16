"""「부산까지」 — top-view real-time sword fight (PRD v4.3+, DESIGN_LOCK).

    .venv\\Scripts\\python.exe src\\main.py

WASD move, left button: hold to raise the weapon and aim (head / torso / legs under the cursor), let go to strike, Space roll, E pick up / leave, 1 bandage,
Tab bag (inventory), mouse wheel zoom, R restart, F2 infected senses on/off, F3 realistic look on/off, Esc quit.
(Right button time crawl with exposure is switched off for now: settings.EXPOSURE_ON.)
The earlier 2.5D street game and the prototypes are kept in src/legacy/ (not imported).
"""

import sys

import pico2d
import sdl2
from pico2d import pico2d as canvas

import bag_screen
import ui
from play import Game
from settings import EXPOSURE_ON, HEIGHT, WIDTH


def bag_mouse(game, event):
    """Hover chooses, a left drag moves a thing between the sheet and the ground, right = use."""
    if event.type == sdl2.SDL_MOUSEMOTION:
        bag_screen.mouse_move(game, event.x, event.y)
    elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
        bag_screen.mouse_down(game, event.x, event.y, "right" if event.button == sdl2.SDL_BUTTON_RIGHT else "left")
    elif event.button == sdl2.SDL_BUTTON_LEFT:
        bag_screen.mouse_up(game, event.x, event.y)


def main(window_x=None):
    """Open the window and run the game loop (Esc quits)."""
    pico2d.open_canvas(WIDTH, HEIGHT, sync=True)
    if window_x is not None:
        sdl2.SDL_SetWindowPosition(canvas.window, window_x, 120)
    sdl2.SDL_SetWindowTitle(canvas.window, "부산까지".encode("utf-8"))
    ui.enable_blending()
    game = Game()
    last = pico2d.get_time()
    running = True
    while running:
        now = pico2d.get_time()
        dt = min(0.05, now - last)
        last = now
        keys = sdl2.SDL_GetKeyboardState(None)
        for event in pico2d.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_KEYDOWN and event.key == sdl2.SDLK_ESCAPE:
                if game.bag_open:
                    game.bag_open = False          # Esc closes the bag first
                else:
                    running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                game.key_down(event.key, keys)
            elif game.bag_open and event.type in (sdl2.SDL_MOUSEMOTION, sdl2.SDL_MOUSEBUTTONDOWN,
                                                  sdl2.SDL_MOUSEBUTTONUP):
                bag_mouse(game, event)               # the bag takes the mouse while it is open
            elif event.type == sdl2.SDL_MOUSEWHEEL and event.y:
                game.wheel(event.y)                  # zoom in / out
            elif event.type == sdl2.SDL_MOUSEMOTION:
                game.aim = (event.x, event.y)
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_LEFT:
                game.press(event.x, event.y)             # raise the weapon, aim with the cursor
            elif event.type == sdl2.SDL_MOUSEBUTTONUP and event.button == sdl2.SDL_BUTTON_LEFT:
                game.release(event.x, event.y)           # the blow
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_RIGHT and EXPOSURE_ON:
                game.slow = True
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_RIGHT:
                game.right_click(event.x, event.y)       # shove (time crawl is off for now)
            elif event.type == sdl2.SDL_MOUSEBUTTONUP and event.button == sdl2.SDL_BUTTON_RIGHT:
                game.slow = False
        game.update(dt, keys)
        pico2d.clear_canvas()
        game.draw()
        pico2d.update_canvas()
    pico2d.close_canvas()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
