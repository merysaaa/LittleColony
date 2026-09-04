"""
Nilo, the Explorer (GDD section 5 - Nilo).

Same deliberately-dumb hardcoded FSM style as TimoAgent - this proves
the perceive -> decide -> act seam scales to a second, independent
purpose without any new agent-framework code. Nilo never checks
Timo's state or the rock directly; he only checks whether the bridge
is repaired and whether a path currently exists, exactly like Timo
only checks the repair position's reachability. The bridge being
repaired is itself a consequence of the rock being moved - Nilo
reacting to it is a second link in the same causal chain, not a
separate hardcoded trigger.
"""
from entities.agent import Agent
from systems.pathfinding import find_path
import settings as s


class NiloAgent(Agent):
    def __init__(self, tile_pos, world):
        super().__init__("Nilo", tile_pos)
        self.color = s.NILO_COLOR
        self.primary_purpose = "Explore accessible territory and discover useful resources"
        self.fsm_state = "IDLE"
        # The west-bank tile beside the bridge doubles as Nilo's "looking
        # east" waiting spot (env doc 11: "repeatedly approaches the
        # damaged bridge and looks east"). Fine to share with Timo's
        # repair spot for Milestone-scope collision simplicity (GDD 19).
        self.riverbank_lookout = world.repair_position
        self.seed_tiles = world.seeds.tiles

    def perceive(self, world):
        base = super().perceive(world)

        nearest_seed = self.seed_tiles[0] if self.seed_tiles else None
        path = find_path(self.tile_pos, nearest_seed, world.is_walkable) if nearest_seed else []
        path_available = bool(path) or self.tile_pos == nearest_seed

        base.update({
            "seeds_discovered": world.seeds.discovered,
            "nearest_seed": nearest_seed,
            "path_to_seeds_available": path_available,
            "at_seed_area": self.tile_pos == nearest_seed,
            "at_riverbank": self.tile_pos == self.riverbank_lookout,
        })
        return base

    def decide(self, perception):
        """
        Hardcoded FSM (mirrors Timo's structure - GDD 20.1 style):
        IDLE -> SEEDS_DISCOVERED?
          yes -> ROUTINE
          no  -> PATH_TO_SEEDS_AVAILABLE?
                   no  -> WAIT_AT_RIVER (bridge still broken)
                   yes -> AT_SEED_AREA?
                            no  -> TRAVEL_TO_SEEDS
                            yes -> DISCOVER_SEEDS
        """
        if perception["seeds_discovered"]:
            self.fsm_state = "ROUTINE_EXPLORE"
            return {"goal": "explore_territory", "action": "idle", "target": None}

        if not perception["path_to_seeds_available"]:
            self.fsm_state = "WAIT_AT_RIVER"
            if perception["at_riverbank"]:
                return {"goal": "discover_seeds", "action": "idle", "target": None}
            return {"goal": "discover_seeds", "action": "move_to", "target": self.riverbank_lookout}

        if not perception["at_seed_area"]:
            self.fsm_state = "TRAVEL_TO_SEEDS"
            return {"goal": "discover_seeds", "action": "move_to", "target": perception["nearest_seed"]}

        self.fsm_state = "DISCOVER_SEEDS"
        return {"goal": "discover_seeds", "action": "discover", "target": perception["nearest_seed"]}

    def _apply_action(self, world):
        super()._apply_action(world)

        if self.current_action == "discover" and self.tile_pos == self.target:
            world.discover_seeds()
