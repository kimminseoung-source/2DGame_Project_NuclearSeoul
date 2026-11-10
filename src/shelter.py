"""The side-view starting shelter."""


from tile_map import WIDTH, TileMap


SHELTER_SPAWN = (154, 78)
SHELTER_EXIT = (724, 103)


class ShelterMap(TileMap):
    width = WIDTH
    has_wreck = False
    left_edge = 25
    right_edge = 746
