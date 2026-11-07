"""The side-view starting shelter."""


from tile_map import WIDTH, TileMap


SHELTER_SPAWN = (154, 78)
SHELTER_SUPPLY = (350, 61)
SHELTER_EXIT = (724, 103)


class ShelterMap(TileMap):
    width = WIDTH
    left_edge = 25
    right_edge = 746
