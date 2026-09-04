"""
Ecosystem Harmony indicator (GDD section 11).
"""

STABLE_HARMONY_TARGET = 91  # GDD 12.2 - the full formula's maximum


def compute_harmony(world):
    harmony = 42
    if world.rock.position != world._initial_rock_pos:
        harmony += 8   # builder_can_access_bridge
    if world.bridge.is_repaired:
        harmony += 12  # bridge_repaired
    if world.seeds.discovered:
        harmony += 8   # seeds_discovered
    if world.farm.total_harvested > 0:
        harmony += 11  # farmer_producing_food
    if world.total_food_distributed > 0:
        harmony += 10  # caretaker_distributing_food
    return harmony


class StableStateTracker:
    """
    Detects the GDD 12.3 end condition: Harmony holding at the stable
    target for a short duration, not just touching it for one frame.

    STABLE_HARMONY_TARGET is the sum of every bonus above - there is no
    way to reach it without the rock moved, the bridge repaired, seeds
    discovered, at least one harvest, AND at least one delivery all
    being true at once. So this can't fire on a partial/broken chain
    (GDD 24.1: "stable ending cannot trigger while a required
    dependency is broken") without checking each condition twice.

    Once triggered, `is_stable` latches - the ending message shouldn't
    disappear just because the player nudges the rock back afterward.
    """
    def __init__(self, hold_time=3.0):
        self.hold_time = hold_time
        self.timer = 0.0
        self.is_stable = False

    def update(self, dt, harmony_value):
        if self.is_stable:
            return True
        if harmony_value >= STABLE_HARMONY_TARGET:
            self.timer += dt
            if self.timer >= self.hold_time:
                self.is_stable = True
        else:
            self.timer = 0.0
        return self.is_stable
