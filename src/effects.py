"""Short-lived visual effects that remove themselves from the game world."""

import camera
import game_clock
import game_world
from bat import BAT_IMPACT_TIME, draw_impact


class Impact:
    """The star burst where a bat blow lands."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.time_left = BAT_IMPACT_TIME

    def update(self):
        self.time_left -= game_clock.frame_time
        if self.time_left <= 0:
            game_world.remove_object(self)

    def draw(self):
        draw_impact(self.x - camera.x, self.y + 5, max(0.0, self.time_left))
