"""
World / TileMap module.

Owns terrain and occupancy information (GDD 15.3: "World owns terrain
and occupancy information"). Nothing in here knows about rendering or
agent reasoning - it only answers questions like "is this tile
walkable" and "what changed."
"""
import settings as s


def _build_map_01():
    """
    Hand-authored first-level layout matching GDD section 8.2 zones:
    NW farm+storage, vertical river with a center bridge, SW forest,
    E houses + resource area. A single narrow corridor on the west
    bank leads to the bridge repair position, and the movable rock
    sits in that corridor - a genuine chokepoint, not decoration.
    """
    W, H = s.MAP_WIDTH, s.MAP_HEIGHT
    grid = [[s.GRASS for _ in range(W)] for _ in range(H)]

    # --- River (vertical divider) ---
    river_col = 10
    for y in range(H):
        grid[y][river_col] = s.WATER
        grid[y][river_col + 1] = s.WATER

    # --- Bridge (broken at start) sits mid-river ---
    bridge_row = 9
    bridge_tiles = [(river_col, bridge_row), (river_col + 1, bridge_row)]
    for (x, y) in bridge_tiles:
        grid[y][x] = s.BRIDGE_BROKEN

    # --- Main east-west dirt path approaching the bridge from both sides ---
    for x in range(0, river_col):
        grid[bridge_row][x] = s.DIRT_PATH
    for x in range(river_col + 2, W):
        grid[bridge_row][x] = s.DIRT_PATH

    # --- Farm + storage, northwest ---
    farm_tiles = []
    for y in range(1, 5):
        for x in range(1, 5):
            grid[y][x] = s.FARM_SOIL
            farm_tiles.append((x, y))
    grid[2][6] = s.STORAGE_FLOOR
    grid[3][6] = s.STORAGE_FLOOR
    storage_position = (6, 2)

    # --- Houses, northeast ---
    grid[2][15] = s.HOUSE
    grid[2][16] = s.HOUSE
    # Doorway tile: houses themselves aren't walkable (GDD 8.3), so Eda
    # approaches and delivers from the open tile right beside them -
    # same "adjacent tile, not the resource tile itself" pattern as
    # Timo's repair_position beside the bridge.
    house_position = (14, 2)

    # --- Forest + wood source, southwest. Also forms the north/south
    # walls of Timo's approach corridor so the rock is a true chokepoint. ---
    for y in range(11, 16):
        for x in range(1, 8):
            if (x + y) % 3 != 0:
                grid[y][x] = s.TREE
    grid[13][3] = s.WOOD_RESOURCE
    grid[13][4] = s.WOOD_RESOURCE
    # Guarantee a clear vertical route from the corridor down to the wood,
    # independent of the sparse tree pattern above (which can otherwise
    # accidentally wall off the forest interior).
    for y in range(9, 14):
        grid[y][3] = s.DIRT_PATH if y < 13 else grid[y][3]

    # --- Timo's approach corridor to the bridge repair position ---
    # Repair position: the west-bank tile directly beside the bridge.
    repair_x, repair_y = river_col - 1, bridge_row
    corridor_y = bridge_row
    # Wall off rows above and below the corridor (not just the two
    # immediately adjacent rows) so row `corridor_y` is a genuine single-file
    # chokepoint with no way around it, matching the GDD's design rule that
    # the rock "genuinely changes Timo's path availability."
    for x in range(4, river_col):
        for wall_y in (corridor_y - 3, corridor_y - 2, corridor_y - 1,
                       corridor_y + 1, corridor_y + 2, corridor_y + 3):
            grid[wall_y][x] = s.TREE
        grid[corridor_y][x] = s.DIRT_PATH

    # --- Eastern resource area (seeds), initially just visible ---
    # Tiles are visible from the start (GDD 8.2/4.8: no fog of war), but
    # the *resource itself* isn't discovered until Nilo reaches it -
    # that's tracked separately in World.seeds, not baked into the grid.
    seed_tiles = []
    for y in range(11, 15):
        for x in range(14, 18):
            if (x + y) % 4 == 0:
                grid[y][x] = s.SEED_RESOURCE
                seed_tiles.append((x, y))

    # --- Rock: placed inside the corridor, blocking Timo's only route ---
    rock_pos = (7, corridor_y)
    # Carve a single alcove beside the rock's tile so the player has
    # somewhere legal to push it to - otherwise the chokepoint has no
    # adjacent open tile at all.
    grid[corridor_y - 1][rock_pos[0]] = s.GRASS

    return (grid, bridge_tiles, repair_x, repair_y, rock_pos, seed_tiles,
            farm_tiles, storage_position, house_position)


class Bridge:
    def __init__(self, tiles):
        self.tiles = tiles          # list of (x, y)
        self.state = "broken"       # broken / repairing / repaired
        self.repair_timer = 0.0
        self.wood_delivered = 0

    @property
    def is_repaired(self):
        return self.state == "repaired"


class MovableRock:
    def __init__(self, position):
        self.position = position    # (x, y)
        self.placed = True


class Resource:
    """
    A resource an agent can find or use somewhere in the world
    (GDD 16.3 / 9). `discovered` starts False for resources an agent
    has to find first (the seeds across the river) and True for ones
    the colony already knows about (the forest's wood).
    """
    def __init__(self, kind, tiles, discovered=True):
        self.kind = kind
        self.tiles = tiles          # list of (x, y) source locations
        self.discovered = discovered


class Storage:
    """
    The colony's shared resource counts (GDD 16.3 / 4.2 storage node).
    Mara deposits food here; Eda draws it down when she distributes it.
    """
    def __init__(self):
        self.food = 0
        self.seeds = 0


class Farm:
    """
    Mara's growing plot (GDD 14 farm.crop_state / 4.1 farm zone).
    crop_state cycles empty -> planted -> growing -> mature -> empty.
    `total_harvested` never resets - it's a durable record that Mara has
    actually produced food, independent of how much Eda later withdraws.
    """
    def __init__(self, tiles):
        self.tiles = tiles          # list of (x, y) farm-soil positions
        self.crop_state = "empty"
        self.grow_timer = 0.0
        self.total_harvested = 0


class World:
    def __init__(self):
        (grid, bridge_tiles, repair_x, repair_y, rock_pos, seed_tiles,
         farm_tiles, storage_position, house_position) = _build_map_01()
        self.grid = grid
        self.bridge = Bridge(bridge_tiles)
        self.rock = MovableRock(rock_pos)
        self.repair_position = (repair_x, repair_y)
        self.wood = Resource("wood", tiles=[(3, 13), (4, 13)], discovered=True)
        self.seeds = Resource("seeds", tiles=seed_tiles, discovered=False)
        self.storage = Storage()
        self.farm = Farm(farm_tiles)
        self.storage_position = storage_position
        self.house_position = house_position
        # Durable count of completed deliveries - unlike storage.food this
        # never decreases, so Harmony's caretaker_distributing_food term
        # (systems/harmony.py) reflects "Eda has distributed at least
        # once" rather than flickering with the current storage level.
        self.total_food_distributed = 0
        self._initial_rock_pos = rock_pos

        # Simple event log other systems can read/clear each frame.
        self.events = []

    # ---- Queries ----------------------------------------------------

    def in_bounds(self, x, y):
        return 0 <= x < s.MAP_WIDTH and 0 <= y < s.MAP_HEIGHT

    def is_walkable(self, x, y):
        if not self.in_bounds(x, y):
            return False

        # Dynamic override: the movable rock blocks its tile while placed.
        if self.rock.placed and (x, y) == self.rock.position:
            return False

        # Dynamic override: bridge tiles walkable only once repaired.
        if (x, y) in self.bridge.tiles:
            return self.bridge.is_repaired

        base_tile = self.grid[y][x]
        return base_tile in s.BASE_WALKABLE_TILES

    def blocked_tiles(self):
        blocked = set()
        for y in range(s.MAP_HEIGHT):
            for x in range(s.MAP_WIDTH):
                if not self.is_walkable(x, y):
                    blocked.add((x, y))
        return blocked

    # ---- Mutations ----------------------------------------------------

    def try_move_rock(self, new_pos):
        """Player-driven: relocate the rock to a legal adjacent tile."""
        x, y = new_pos
        if not self.in_bounds(x, y):
            return False
        if (x, y) == self.rock.position:
            return False
        if (x, y) in self.bridge.tiles:
            return False
        if not self.is_walkable_ignoring_rock(x, y):
            return False
        self.rock.position = (x, y)
        self.events.append({"type": "OBJECT_MOVED", "object": "rock", "to": (x, y)})
        return True

    def is_walkable_ignoring_rock(self, x, y):
        if not self.in_bounds(x, y):
            return False
        if (x, y) in self.bridge.tiles:
            return self.bridge.is_repaired
        return self.grid[y][x] in s.BASE_WALKABLE_TILES

    def deliver_wood_to_bridge(self):
        self.bridge.wood_delivered += 1
        self.events.append({"type": "AGENT_DROPPED_RESOURCE", "resource": "wood"})
        if self.bridge.wood_delivered >= s.BRIDGE_REPAIR_WOOD_REQUIRED:
            self.bridge.state = "repairing"
            self.events.append({"type": "BRIDGE_REPAIR_STARTED"})

    def discover_seeds(self):
        if not self.seeds.discovered:
            self.seeds.discovered = True
            self.events.append({"type": "RESOURCE_DISCOVERED", "resource": "seeds"})

    def deposit_food(self, amount=1):
        self.storage.food += amount
        self.events.append({"type": "FOOD_STORED", "amount": amount})

    def withdraw_food(self, amount=1):
        """Take food out of storage to carry it (GDD: Eda collects food)."""
        if self.storage.food < amount:
            return False
        self.storage.food -= amount
        self.events.append({"type": "AGENT_COLLECTED_RESOURCE", "resource": "food"})
        return True

    def deliver_food_to_house(self):
        """Complete a delivery (GDD: Eda distributes resources to a house)."""
        self.total_food_distributed += 1
        self.events.append({"type": "FOOD_DISTRIBUTED", "amount": 1})

    def plant_seeds(self):
        if self.farm.crop_state != "empty":
            return False
        self.farm.crop_state = "planted"
        self.farm.grow_timer = 0.0
        self.events.append({"type": "AGENT_STARTED_ACTION", "action": "plant_seeds"})
        return True

    def harvest_crop(self):
        if self.farm.crop_state != "mature":
            return False
        self.farm.crop_state = "empty"
        self.farm.total_harvested += 1
        self.events.append({"type": "AGENT_COLLECTED_RESOURCE", "resource": "food"})
        return True

    def update(self, dt):
        if self.bridge.state == "repairing":
            self.bridge.repair_timer += dt
            if self.bridge.repair_timer >= s.BRIDGE_REPAIR_TIME:
                self.bridge.state = "repaired"
                self.events.append({"type": "BRIDGE_REPAIRED"})

        if self.farm.crop_state == "planted":
            self.farm.grow_timer += dt
            if self.farm.grow_timer >= s.FARM_PLANT_TO_GROWING_TIME:
                self.farm.crop_state = "growing"
                self.farm.grow_timer = 0.0
        elif self.farm.crop_state == "growing":
            self.farm.grow_timer += dt
            if self.farm.grow_timer >= s.FARM_GROWING_TO_MATURE_TIME:
                self.farm.crop_state = "mature"
                self.events.append({"type": "AGENT_COMPLETED_ACTION", "action": "crop_matured"})

    def pop_events(self):
        events, self.events = self.events, []
        return events
