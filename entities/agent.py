"""
Base Agent (GDD 16.1 + 17 + 20.2).

This is the seam. `perceive()` builds a plain dict describing what the
agent can currently sense. `decide()` is expected to return a plain
dict shaped like {"goal": ..., "action": ...}. Everything downstream
(`act`) only reads that dict - it never assumes *how* it was produced.

For Milestone 1, `decide()` is a hardcoded finite-state machine
(see TimoAgent). Later, this exact method can be replaced by a call
into the real purpose-network / DBN reasoner without touching
perceive(), act(), rendering, or pathfinding at all - as long as the
returned dict keeps this shape.
"""
import settings as s
from systems.pathfinding import find_path


class Agent:
    def __init__(self, name, tile_pos):
        self.name = name
        self.tile_pos = tile_pos          # logical (x, y) tile coords
        self.pixel_pos = [
            tile_pos[0] * s.TILE_SIZE, tile_pos[1] * s.TILE_SIZE
        ]
        self.direction = "down"

        # Purposeful state (GDD 16.1)
        self.primary_purpose = None
        self.current_goal = None
        self.current_action = None
        self.target = None

        # Navigation
        self.path = []
        self.blocked = False
        self._move_timer = 0.0

        # Resources / memory
        self.inventory = []
        self.needs = {}
        self.memory = {}

        # Debug/observation friendly state
        self.last_decision = {}
        self._replan_timer = 0.0

    # ---- The seam: perceive -> decide -> act -------------------------

    def perceive(self, world):
        """
        Build the perception dict handed to decide(). Deliberately
        plain data - no world/pygame objects - so this boundary can
        later be serialized across a process/network if the real
        agent reasoner runs elsewhere (open question for the prof).
        """
        return {
            "position": self.tile_pos,
            "inventory": list(self.inventory),
        }

    def decide(self, perception):
        """
        Placeholder decision function. Subclasses (or, later, an
        external reasoning system) override this. Must return a dict
        shaped like {"goal": str, "action": str, "target": (x,y) or None}.
        """
        return {"goal": None, "action": "idle", "target": None}

    def update(self, world, dt):
        self._replan_timer += dt

        perception = self.perceive(world)

        # Replan on an interval rather than every frame (GDD Appendix A:
        # AGENT_REPLAN_INTERVAL), matching how a heavier reasoning system
        # (e.g. a Bayesian update) would realistically be paced.
        if self._replan_timer >= s.AGENT_REPLAN_INTERVAL or self.action_finished_or_invalid():
            self._replan_timer = 0.0
            decision = self.decide(perception)
            self.last_decision = decision
            self.current_goal = decision.get("goal")
            self.current_action = decision.get("action")
            self.target = decision.get("target")
            self._apply_action(world)

        self._advance_movement(world, dt)

    def action_finished_or_invalid(self):
        return not self.path and self.target is not None

    # ---- Movement -----------------------------------------------------

    def _apply_action(self, world):
        """Translate the chosen action into a concrete path, if needed."""
        if self.current_action in ("move_to", "seek_alternate_access") and self.target:
            path = find_path(self.tile_pos, self.target, world.is_walkable)
            if path:
                self.path = path
                self.blocked = False
            else:
                self.path = []
                self.blocked = True

    def _advance_movement(self, world, dt):
        if not self.path:
            return
        self._move_timer += dt
        if self._move_timer < s.AGENT_MOVE_TILE_TIME:
            return
        self._move_timer = 0.0

        next_tile = self.path[0]
        if not world.is_walkable(*next_tile):
            # World changed under us (e.g. rock moved back) - replan next tick.
            self.path = []
            self.blocked = True
            return

        dx = next_tile[0] - self.tile_pos[0]
        dy = next_tile[1] - self.tile_pos[1]
        if dx > 0: self.direction = "right"
        elif dx < 0: self.direction = "left"
        elif dy > 0: self.direction = "down"
        elif dy < 0: self.direction = "up"

        self.tile_pos = next_tile
        self.pixel_pos = [next_tile[0] * s.TILE_SIZE, next_tile[1] * s.TILE_SIZE]
        self.path.pop(0)
