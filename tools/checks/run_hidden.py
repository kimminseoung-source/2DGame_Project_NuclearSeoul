"""Run a check script with the game window hidden (2026-11-16: windows popping up in front got in
the user's way). pico2d makes its window with SDL_CreateWindow; this adds SDL_WINDOW_HIDDEN.
    python run_hidden.py <script.py> [args...]"""
import runpy, sys
import sdl2
import pico2d.pico2d as p2
_create = p2.SDL_CreateWindow
def hidden(title, x, y, w, h, flags):
    return _create(title, x, y, w, h, (flags | sdl2.SDL_WINDOW_HIDDEN) & ~sdl2.SDL_WINDOW_SHOWN)
p2.SDL_CreateWindow = hidden
script = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")
