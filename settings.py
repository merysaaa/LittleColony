"""Global constants. Matches GDD Appendix A - Prototype Constants."""

TILE_SIZE = 32
MAP_WIDTH = 20
MAP_HEIGHT = 20
TARGET_FPS = 60

SCREEN_WIDTH = MAP_WIDTH * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE

PLAYER_INTERACTION_RANGE = 1        # tiles
AGENT_REPLAN_INTERVAL = 0.5         # seconds
AGENT_MOVE_TILE_TIME = 0.25         # seconds to cross one tile
PLAYER_SPEED = 140                  # pixels/second

BRIDGE_REPAIR_WOOD_REQUIRED = 3
BRIDGE_REPAIR_TIME = 5.0            # seconds

FARM_PLANT_TO_GROWING_TIME = 1.5    # seconds, example
FARM_GROWING_TO_MATURE_TIME = 1.5   # seconds, example

# --- Tile IDs (GDD 8.1) ---
GRASS = 0
DIRT_PATH = 1
FARM_SOIL = 2
WATER = 3
TREE = 4
ROCK_STATIC = 5
ROCK_MOVABLE = 6
BRIDGE_BROKEN = 7
BRIDGE_REPAIRED = 8
STORAGE_FLOOR = 9
HOUSE = 10
FLOWER = 11
SEED_RESOURCE = 12
WOOD_RESOURCE = 13
FOOD_RESOURCE = 14

# Base terrain tiles that are walkable on their own (before dynamic overrides
# like the movable rock or bridge state are applied).
BASE_WALKABLE_TILES = {
    GRASS, DIRT_PATH, FARM_SOIL, STORAGE_FLOOR,
    FLOWER, SEED_RESOURCE, WOOD_RESOURCE, FOOD_RESOURCE,
}

# Simple flat color palette so the game runs before any real art exists,
# per GDD 5.5: "behavior system should be able to run even if all
# characters are temporarily rendered as colored squares."
TILE_COLORS = {
    GRASS: (99, 163, 79),
    DIRT_PATH: (176, 140, 92),
    FARM_SOIL: (110, 78, 51),
    WATER: (69, 128, 191),
    TREE: (43, 99, 56),
    ROCK_STATIC: (120, 120, 120),
    ROCK_MOVABLE: (150, 130, 110),
    BRIDGE_BROKEN: (110, 90, 60),
    BRIDGE_REPAIRED: (170, 130, 80),
    STORAGE_FLOOR: (200, 180, 120),
    HOUSE: (150, 90, 70),
    FLOWER: (220, 130, 170),
    SEED_RESOURCE: (210, 200, 90),
    WOOD_RESOURCE: (120, 80, 40),
    FOOD_RESOURCE: (220, 90, 70),
}

PLAYER_COLOR = (250, 250, 250)
TIMO_COLOR = (230, 160, 40)
NILO_COLOR = (90, 140, 200)
MARA_COLOR = (110, 190, 90)
EDA_COLOR = (200, 90, 160)
HARMONY_TEXT_COLOR = (30, 30, 30)
DEBUG_TEXT_COLOR = (255, 255, 0)
