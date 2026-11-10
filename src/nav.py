"""Hidden navigation field for free combat movement, measured in metres.

The street floor is sampled with a fine lattice of nodes the player never sees.
Searches run over that lattice with metre costs, then the route is pulled
straight, so movement looks free like BG3 while the maths stays simple.
"""

import heapq
from math import hypot



# 1.5 m equals the old 48 px cell. The floor's depth axis is foreshortened 2:1,
# so a pixel of depth covers twice the distance of a pixel across.
PX_PER_M_X = 32.0
PX_PER_M_Y = 16.0
NODE_X = 8          # 0.25 m across
NODE_Y = 4          # 0.25 m of depth
CLEARANCE = 8       # px kept from the wreck and the floor edges, as before
BODY_GAP_M = 0.9    # two bodies never stand closer than this
# Sprites are ~30 px wide, so bodies also keep this box apart on screen
# (otherwise one character could stand right on top of another in depth).
BODY_BOX_X = 24
BODY_BOX_Y = 22
SAMPLE_PX = 3
NEIGHBOURS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def metres(a, b):
    return hypot((b[0] - a[0]) / PX_PER_M_X, (b[1] - a[1]) / PX_PER_M_Y)


def bodies_clash(a, b):
    if metres(a, b) < BODY_GAP_M:
        return True
    return abs(a[0] - b[0]) < BODY_BOX_X and abs(a[1] - b[1]) < BODY_BOX_Y


def path_length(points):
    return sum(metres(a, b) for a, b in zip(points, points[1:]))


def point_along(points, distance_m):
    """The point reached after walking distance_m along a polyline."""
    for a, b in zip(points, points[1:]):
        step = metres(a, b)
        if distance_m <= step:
            t = distance_m / step if step else 0.0
            return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        distance_m -= step
    return points[-1]


def truncate(points, budget_m):
    """Cut a polyline so its length does not exceed the budget."""
    kept, used = [points[0]], 0.0
    for a, b in zip(points, points[1:]):
        step = metres(a, b)
        if used + step <= budget_m:
            kept.append(b)
            used += step
            continue
        rest = budget_m - used
        if rest > 0.05:
            t = rest / step
            kept.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        break
    return kept


class NavField:
    """Walkable lattice covering the screen area where combat started."""

    def __init__(self, tile_map, left, right):
        self.tile_map = tile_map
        self.left, self.right = left, right
        self.columns = int((right - left) // NODE_X)
        self.y0 = tile_map.floor_bottom + CLEARANCE
        self.rows = int((tile_map.floor_top - CLEARANCE - self.y0) // NODE_Y) + 1
        self.static = {
            (c, r) for c in range(self.columns) for r in range(self.rows)
            if tile_map.can_stand(*self.position((c, r)), CLEARANCE)
        }

    def position(self, node):
        c, r = node
        return self.left + NODE_X / 2 + c * NODE_X, self.y0 + r * NODE_Y

    def node_at(self, point):
        return (round((point[0] - self.left - NODE_X / 2) / NODE_X), round((point[1] - self.y0) / NODE_Y))

    def open_at(self, point, blockers):
        x, y = point
        if not (self.left <= x <= self.right and self.tile_map.can_stand(x, y, CLEARANCE)):
            return False
        return not any(bodies_clash(point, b) for b in blockers)

    def blocked_nodes(self, blockers):
        return {n for n in self.static if any(bodies_clash(self.position(n), b) for b in blockers)}

    def nearest_open(self, point, blockers=()):
        blocked = self.blocked_nodes(blockers)
        nodes = [n for n in self.static if n not in blocked]
        return min(nodes, key=lambda n: metres(self.position(n), point), default=None)

    def search(self, start, blockers, limit=None):
        """Dijkstra from a point: {node: (cost in metres, previous node)}."""
        blocked = self.blocked_nodes(blockers)
        origin = min(self.static, key=lambda n: metres(self.position(n), start))
        costs = {origin: (metres(start, self.position(origin)), None)}
        queue = [(costs[origin][0], origin)]
        while queue:
            cost, node = heapq.heappop(queue)
            if cost > costs[node][0]:
                continue
            for dx, dy in NEIGHBOURS:
                step = node[0] + dx, node[1] + dy
                if step not in self.static or step in blocked:
                    continue
                if dx and dy and ((node[0] + dx, node[1]) not in self.static
                                  or (node[0], node[1] + dy) not in self.static):
                    continue
                new_cost = cost + metres(self.position(node), self.position(step))
                if limit is not None and new_cost > limit:
                    continue
                if step not in costs or new_cost < costs[step][0] - 1e-9:
                    costs[step] = (new_cost, node)
                    heapq.heappush(queue, (new_cost, step))
        return costs

    def route(self, start, goal, costs, blockers):
        """Straightened polyline from start to a searched node."""
        nodes = []
        node = goal
        while node is not None:
            nodes.append(node)
            node = costs[node][1]
        # The search may start from a lattice point inside another body; never route through one.
        points = [start] + [self.position(n) for n in reversed(nodes)
                            if self.open_at(self.position(n), blockers)]
        # Pull the string: jump to the farthest point still reachable in a straight line.
        pulled, index = [points[0]], 0
        while index < len(points) - 1:
            far = len(points) - 1
            while far > index + 1 and not self.segment_clear(points[index], points[far], blockers):
                far -= 1
            pulled.append(points[far])
            index = far
        return pulled

    def segment_clear(self, a, b, blockers):
        length = hypot(b[0] - a[0], b[1] - a[1])
        samples = max(1, int(length / SAMPLE_PX))
        for i in range(1, samples + 1):
            t = i / samples
            if not self.open_at((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), blockers):
                return False
        return True
