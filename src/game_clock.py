"""Time of the current frame, read by every object's update() (like game_framework.frame_time).

There are two clocks: the world's (frame_time) and the hero's (hero_frame_time). They are
the same except during the mutation time warp (time_warp.py), when the world crawls and
the hero speeds up.
"""

MAX_STEP = 0.05

frame_time = 0.0
hero_frame_time = 0.0
real_frame_time = 0.0     # unscaled and not stopped by hit-stop: for screen effects


def step():
    """Frame time clamped so a slow frame cannot teleport objects."""
    return min(frame_time, MAX_STEP)


def hero_step():
    return min(hero_frame_time, MAX_STEP)
