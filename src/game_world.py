"""Layered game world, following the course's game_world module (LEC14).

Every object put here has update() and draw(). Layers are drawn in order;
objects on the GROUND layer are sorted by depth so farther ones are drawn first.
"""

import screen_shake
import ui


# Layers, back to front. BOTTOM is the hotbar strip under the street.
BACKGROUND, BOARD, GROUND, EFFECT, OVERLAY, HUD, POPUP, BOTTOM = range(8)
SHAKEN = range(HUD)     # the street and what is drawn on it; the HUD and pop-ups stay put
world = [[] for _ in range(BOTTOM + 1)]


def add_object(o, depth):
    world[depth].append(o)


def add_objects(objects, depth):
    world[depth] += objects


def remove_object(o):
    for layer in world:
        if o in layer:
            layer.remove(o)
            return
    raise ValueError("Object not found in the game world")


def contains(o):
    return any(o in layer for layer in world)


def clear():
    for layer in world:
        layer.clear()


def update():
    # Copy each layer so objects may remove themselves while updating.
    for layer in world:
        for o in layer[:]:
            o.update()


def render():
    ui.begin_world(*screen_shake.offset())
    for depth in range(BOTTOM):
        if depth == HUD:
            ui.begin_world()
        layer = world[depth]
        if depth == GROUND:
            layer = sorted(layer, key=lambda o: getattr(o, "y", 0), reverse=True)
        for o in layer:
            o.draw()
    ui.begin_bottom()
    for o in world[BOTTOM]:
        o.draw()
    ui.end_regions()
