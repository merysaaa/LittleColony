"""
Timo, the Builder (GDD section 5 - Timo, and 20.1 - example state machine).

IMPORTANT: this is a deliberately dumb, hardcoded FSM. It exists only
to prove the perceive -> decide -> act pipeline end to end for
Milestone 1. It does NOT demonstrate agency freedom or Platonic
freedom in the sense the research paper means - it's a lookup table,
which is exactly the kind of thing that paper is trying to move past.
This whole class's decide() method is the intended replacement point.
"""
from entities.agent import Agent
import settings as s


class TimoAgent(Agent):
    def __init__(self, tile_pos, world):
        super().__init__("Timo", tile_pos)
        self.color = s.TIMO_COLOR
        self.primary_purpose = "Maintain essential colony infrastructure"
        self.fsm_state = "IDLE"
        self.repair_position = world.repair_position
        self.wood_source_tiles = world.wood.tiles

    def perceive(self, world):
        base = super().perceive(world)
        path_to_repair = None
        blocked = True
        # Cheap reachability probe; real pathing happens in _apply_action.
        from systems.pathfinding import find_path
        path = find_path(self.tile_pos, self.repair_position, world.is_walkable)
        if path or self.tile_pos == self.repair_position:
            blocked = False

        base.update({
            "bridge_state": world.bridge.state,
            "wood_delivered": world.bridge.wood_delivered,
            "wood_required": s.BRIDGE_REPAIR_WOOD_REQUIRED,
            "path_to_repair_available": not blocked,
            "at_repair_position": self.tile_pos == self.repair_position,
            "carrying_wood": "wood" in self.inventory,
        })
        return base

    def decide(self, perception):
        """
        Hardcoded FSM (GDD 20.1):
        IDLE -> CHECK_INFRASTRUCTURE -> NEED_REPAIR?
          no  -> ROUTINE
          yes -> NEED_WOOD? yes -> GET_WOOD
                              no  -> GO_TO_BRIDGE -> PATH_AVAILABLE?
                                       no  -> BLOCKED/RETRY
                                       yes -> REPAIR_BRIDGE
        """
        bridge_state = perception["bridge_state"]

        if bridge_state == "repaired":
            self.fsm_state = "ROUTINE"
            return {"goal": "routine_maintenance", "action": "idle", "target": None}

        if bridge_state == "repairing":
            self.fsm_state = "WAIT_FOR_REPAIR"
            return {"goal": "repair_bridge", "action": "idle", "target": None}

        # bridge is "broken" from here on
        need_wood = not perception["carrying_wood"] and perception["wood_delivered"] < perception["wood_required"]

        if need_wood:
            self.fsm_state = "GET_WOOD"
            nearest_wood = self.wood_source_tiles[0]
            return {"goal": "repair_bridge", "action": "move_to", "target": nearest_wood}

        if not perception["path_to_repair_available"] and not perception["at_repair_position"]:
            self.fsm_state = "BLOCKED"
            return {"goal": "repair_bridge", "action": "seek_alternate_access", "target": self.repair_position}

        if not perception["at_repair_position"]:
            self.fsm_state = "GO_TO_BRIDGE"
            return {"goal": "repair_bridge", "action": "move_to", "target": self.repair_position}

        self.fsm_state = "REPAIR_BRIDGE"
        return {"goal": "repair_bridge", "action": "repair", "target": self.repair_position}

    def _apply_action(self, world):
        super()._apply_action(world)

        if self.current_action == "repair" and self.tile_pos == self.repair_position:
            world.deliver_wood_to_bridge()
            self.inventory.clear()

        # Pick up wood once we've arrived at a wood-source tile.
        if self.current_action == "move_to" and self.target in self.wood_source_tiles:
            if self.tile_pos == self.target and "wood" not in self.inventory:
                self.inventory.append("wood")
