"""「부산까지」 — top-view real-time sword fight (PRD v4.3+, DESIGN_LOCK).

    .venv\\Scripts\\python.exe src\\main.py

WASD move, left click slash toward the mouse, Space roll, right button held slows time
(exposure rises), R restart, F2 infected senses on/off (compare), Esc quit.
The earlier 2.5D street game and the prototypes are kept in src/legacy/ (not imported).
"""

import sys

import pico2d
import sdl2
from pico2d import pico2d as canvas

import ui
from play import Game
from settings import HEIGHT, WIDTH


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
            if event.type == sdl2.SDL_QUIT or (event.type == sdl2.SDL_KEYDOWN and event.key == sdl2.SDLK_ESCAPE):
                running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                game.key_down(event.key, keys)
            elif event.type == sdl2.SDL_MOUSEMOTION:
                game.aim = (event.x, event.y)
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_LEFT:
                game.click(event.x, event.y)
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_RIGHT:
                game.slow = True
            elif event.type == sdl2.SDL_MOUSEBUTTONUP and event.button == sdl2.SDL_BUTTON_RIGHT:
                game.slow = False
        game.update(dt, keys)
        pico2d.clear_canvas()
        game.draw()
        pico2d.update_canvas()
    pico2d.close_canvas()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
