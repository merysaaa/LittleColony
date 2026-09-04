"""
Grid-based pathfinding (GDD section 18).
BFS is explicitly acceptable for a 20x20 map per the design doc;
A* would only matter at much larger scale.
"""
from collections import deque


def find_path(start, goal, is_walkable):
    """
    start, goal: (x, y) tile coordinates
    is_walkable: callable(x, y) -> bool
    Returns a list of (x, y) tiles from the first step after `start`
    to `goal` inclusive, or [] if unreachable.
    """
    if start == goal:
        return []

    frontier = deque([start])
    came_from = {start: None}

    while frontier:
        current = frontier.popleft()
        if current == goal:
            break
        cx, cy = current
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (cx + dx, cy + dy)
            if nxt in came_from:
                continue
            if nxt != goal and not is_walkable(*nxt):
                continue
            if nxt == goal and not is_walkable(*nxt):
                # Goal tile itself must also be walkable (e.g. repair spot).
                continue
            came_from[nxt] = current
            frontier.append(nxt)

    if goal not in came_from:
        return []

    path = []
    node = goal
    while node != start:
        path.append(node)
        node = came_from[node]
    path.reverse()
    return path
