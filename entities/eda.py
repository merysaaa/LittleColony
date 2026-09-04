"""
Eda, the Caretaker (GDD section 5 - Eda).

Same FSM seam as the other three. Eda only perceives world.storage.food
and her own inventory - she never calls into Mara's code. Mara filling
storage is what changes what Eda perceives; the causal link runs
entirely through World, never a direct call between agents.
"""
from entities.agent import Agent
import settings as s


class EdaAgent(Agent):
    def __init__(self, tile_pos, world):
        super().__init__("Eda", tile_pos)
        self.color = s.EDA_COLOR
        self.primary_purpose = "Support basic needs by moving available resources to where they are needed"
        self.fsm_state = "IDLE"
        self.storage_position = world.storage_position
        self.house_position = world.house_position

    def perceive(self, world):
        base = super().perceive(world)
        base.update({
            "storage_food": world.storage.food,
            "carrying_food": "food" in self.inventory,
            "at_storage": self.tile_pos == self.storage_position,
            "at_house": self.tile_pos == self.house_position,
        })
        return base

    def decide(self, perception):
        """
        Hardcoded FSM (mirrors the other agents - GDD 20.1 style):
        CARRYING_FOOD? -> yes -> GO_TO_HOUSE -> DISTRIBUTE
                          no  -> STORAGE_HAS_FOOD?
                                   no  -> WAIT_FOR_FOOD (rechecks on the
                                          normal replan interval - GDD:
                                          "periodically check again
                                          rather than producing food
                                          herself")
                                   yes -> GO_TO_STORAGE -> COLLECT
        """
        if perception["carrying_food"]:
            if not perception["at_house"]:
                self.fsm_state = "GO_TO_HOUSE"
                return {"goal": "distribute_food", "action": "move_to", "target": self.house_position}
            self.fsm_state = "DISTRIBUTE_FOOD"
            return {"goal": "distribute_food", "action": "distribute", "target": self.house_position}

        if perception["storage_food"] <= 0:
            self.fsm_state = "WAIT_FOR_FOOD"
            return {"goal": "distribute_food", "action": "idle", "target": None}

        if not perception["at_storage"]:
            self.fsm_state = "GO_TO_STORAGE"
            return {"goal": "distribute_food", "action": "move_to", "target": self.storage_position}

        self.fsm_state = "COLLECT_FOOD"
        return {"goal": "distribute_food", "action": "collect", "target": self.storage_position}

    def _apply_action(self, world):
        super()._apply_action(world)

        if self.current_action == "collect" and self.tile_pos == self.target:
            if world.withdraw_food(1):
                self.inventory.append("food")

        if self.current_action == "distribute" and self.tile_pos == self.target:
            world.deliver_food_to_house()
            self.inventory.clear()
