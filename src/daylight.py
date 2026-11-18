"""Day and night (2026-11-18 "우선 낮과 밤을 만들고 낮에는 더 잘 보이게끔"): a clock that runs on,
and how dark it is outside the hero's view cone because of it.

- What day and night change for SEEING is only how far the view cone reaches (2026-11-18 "낮과 밤에
  따라 시야 길이만 달라지는 게 좋을 것 같습니다"): DAY_RANGE by day, NIGHT_RANGE at night. The
  infected outside the cone or behind walls are hidden either way (vision_cone.visible).
- What they change for the LOOK: how much the world outside the light is dimmed (FOG_DAY,
  FOG_NIGHT) - streets and buildings stay readable both times.
- Dusk and dawn blend the two over two hours; the night also gets a cold blue tint.
- HOUR real seconds make one hour: a play in an area starts in the afternoon and night falls
  around the time the hero reaches the station.
"""

HOUR = 30.0                 # real s per hour of the day
START = 14.0                # the hour a play starts at
DAWN, DAY, DUSK, NIGHT = 5.0, 7.0, 18.0, 20.0   # light rises DAWN..DAY, falls DUSK..NIGHT
FOG_DAY = 60                # how dim the world is drawn outside the light by day...
FOG_NIGHT = 150             # ...and at night (seeing the infected does not depend on these)
DAY_RANGE = 520             # how far the view cone reaches by day...
NIGHT_RANGE = 300           # ...and at night
NIGHT_TINT = (8, 16, 40, 70)  # rgba laid over the world at full night


class Daylight:
    def __init__(self, hour=START):
        self.hour = hour

    def update(self, dt):
        self.hour = (self.hour + dt / HOUR) % 24

    @property
    def light(self):
        """1 by day, 0 at night, in between at dusk and dawn."""
        h = self.hour
        if DAY <= h < DUSK:
            return 1.0
        if DUSK <= h < NIGHT:
            return 1.0 - (h - DUSK) / (NIGHT - DUSK)
        if DAWN <= h < DAY:
            return (h - DAWN) / (DAY - DAWN)
        return 0.0

    @property
    def reach(self):
        return NIGHT_RANGE + (DAY_RANGE - NIGHT_RANGE) * self.light

    @property
    def fog(self):
        return FOG_NIGHT + (FOG_DAY - FOG_NIGHT) * self.light

    @property
    def name(self):
        h = self.hour
        return "낮" if DAY <= h < DUSK else "저녁" if DUSK <= h < NIGHT else "새벽" if DAWN <= h < DAY else "밤"

    @property
    def clock(self):
        return f"{int(self.hour):02d}:{int(self.hour % 1 * 60):02d}"
