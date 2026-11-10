"""Screen shake: a short jolt of the world view that fades out, after a heavy blow.

Kept as a module like camera.py: there is one screen, so one shake at a time.
"""

import random


strength = 0.0      # pixels at the start of the shake
duration = 0.0
time_left = 0.0


def reset():
    global strength, duration, time_left
    strength = duration = time_left = 0.0


def start(pixels, seconds):
    """Shake the world view; a weaker shake never cuts a stronger one short."""
    global strength, duration, time_left
    if pixels <= 0 or seconds <= 0 or pixels < current():
        return
    strength, duration, time_left = pixels, seconds, seconds


def current():
    return strength * time_left / duration if time_left > 0 else 0.0


def update(frame_time):
    global time_left
    time_left = max(0.0, time_left - frame_time)


def offset():
    """(dx, dy) for the world view, right and up positive.

    SDL draws nothing into a viewport that starts left of or above the window, so the
    jolt only pushes the view right and down (dx >= 0, dy <= 0).
    """
    amount = current()
    if amount <= 0:
        return 0, 0
    return round(random.uniform(0, 2 * amount)), -round(random.uniform(0, 2 * amount))
