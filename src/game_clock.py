"""Time of the current frame, read by every object's update() (like game_framework.frame_time)."""

MAX_STEP = 0.05

frame_time = 0.0


def step():
    """Frame time clamped so a slow frame cannot teleport objects."""
    return min(frame_time, MAX_STEP)
