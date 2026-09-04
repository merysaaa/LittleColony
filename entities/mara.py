"""
Mara, the Farmer (GDD section 5 - Mara).

Same FSM seam as Timo/Nilo. Mara never touches Nilo's code or state -
she only perceives world.seeds.discovered and world.farm.crop_state.
Nilo discovering the seeds is what changes her perception; the causal
link runs entirely through World, never a direct call between agents.
"""
from entities.agent import Agent
import settings as s


class MaraAgent(Agent):
    def __init__(self, tile_pos, world):
        super().__init__("Mara", tile_pos)
        self.color = s.MARA_COLOR
        self.primary_purpose = "Maintain a viable food supply"
        self.fsm_state = "IDLE"
        self.farm_tile = world.farm.tiles[0]
        self.storage_position = world.storage_position

    def perceive(self, world):
        base = super().perceive(world)
        base.update({
            "seeds_discovered": world.seeds.discovered,
            "crop_state": world.farm.crop_state,
            "at_farm": self.tile_pos == self.farm_tile,
            "at_storage": self.tile_pos == self.storage_position,
            "carrying_food": "food" in self.inventory,
        })
        return base

    def decide(self, perception):
        """
        Hardcoded FSM (mirrors Timo/Nilo - GDD 20.1 style):
        CARRYING_FOOD? -> yes -> GO_TO_STORAGE -> DEPOSIT
                          no  -> SEEDS_DISCOVERED?
                                   no  -> WAIT_FOR_SEEDS
                                   yes -> CROP_STATE?
                                            empty          -> GO_TO_FARM -> PLANT
                                            planted/growing -> WAIT_FOR_CROP
                                            mature         -> GO_TO_FARM -> HARVEST
        """
        if perception["carrying_food"]:
            if not perception["at_storage"]:
                self.fsm_state = "GO_TO_STORAGE"
                return {"goal": "deliver_food", "action": "move_to", "target": self.storage_position}
            self.fsm_state = "DEPOSIT_FOOD"
            return {"goal": "deliver_food", "action": "deposit", "target": self.storage_position}

        if not perception["seeds_discovered"]:
            self.fsm_state = "WAIT_FOR_SEEDS"
            return {"goal": "produce_food", "action": "idle", "target": None}

        crop_state = perception["crop_state"]

        if crop_state == "empty":
            self.fsm_state = "GO_TO_FARM"
            if not perception["at_farm"]:
                return {"goal": "produce_food", "action": "move_to", "target": self.farm_tile}
            return {"goal": "produce_food", "action": "plant", "target": self.farm_tile}

        if crop_state == "mature":
            self.fsm_state = "HARVEST"
            if not perception["at_farm"]:
                return {"goal": "produce_food", "action": "move_to", "target": self.farm_tile}
            return {"goal": "produce_food", "action": "harvest", "target": self.farm_tile}

        self.fsm_state = "WAIT_FOR_CROP"  # planted or growing
        return {"goal": "produce_food", "action": "idle", "target": None}

    def _apply_action(self, world):
        super()._apply_action(world)

        if self.current_action == "plant" and self.tile_pos == self.target:
            world.plant_seeds()

        if self.current_action == "harvest" and self.tile_pos == self.target:
            if world.harvest_crop():
                self.inventory.append("food")

        if self.current_action == "deposit" and self.tile_pos == self.target:
            world.deposit_food(1)
            self.inventory.clear()
