# Little Colony — Milestone 1

This is Milestone 1 from the Game Design Document: a 20×20 world with the
player, Timo, wood, the movable rock, and the broken bridge. It proves the
central interaction: **moving the rock changes Timo's autonomous behavior
without any direct command.**

## Run it

```
pip install pygame
python main.py
```

## Controls

| Input          | Action                              |
|----------------|--------------------------------------|
| WASD / Arrows  | Move                                 |
| E / Space      | Interact (move the rock when adjacent) |
| F1             | Toggle debug overlay                 |
| Esc            | Quit                                 |

## What to expect

1. Timo spawns west of the river and immediately starts pursuing his own
   goal (repair the bridge) — nobody commands him.
2. He walks south, collects wood, then tries to reach the bridge repair
   position and gets stuck: a rock blocks the only route (a real
   chokepoint, not a suggestion).
3. Walk up next to the rock (it's south of the main path, in the forest
   corridor) and press E to push it into the alcove beside it.
4. Watch Timo — with no further input from you — detect the new opening,
   walk to the repair position, and repair the bridge. The Ecosystem
   Harmony readout in the top-left updates when this happens.

Toggle F1 any time to see each agent's live goal/action/target and
whether it's currently blocked — this is the same information a future
reasoning system will need to expose.

## Where the real research work plugs in

Everything under `entities/timo.py` — specifically `TimoAgent.decide()` —
is a hardcoded finite-state machine standing in for the real reasoning
system. It exists only to prove the pipeline works. The perception dict
built in `perceive()` and the decision dict returned by `decide()` are
the seam: a purpose-network / DBN reasoner can replace `decide()` entirely
without touching pathfinding, rendering, collision, or the world state —
as long as it keeps returning `{"goal": ..., "action": ..., "target": ...}`.

## Project structure

```
little_colony/
├── main.py              entry point
├── game.py               event loop, input, update order
├── settings.py            constants, tile IDs, colors
├── renderer.py            flat-color rendering (no art yet, by design)
├── world/world.py         terrain, bridge state, rock, walkability
├── entities/agent.py       base perceive -> decide -> act cycle
├── entities/timo.py        Timo's FSM (the placeholder to replace later)
├── entities/player.py      player movement + collision
└── systems/
    ├── pathfinding.py       BFS
    └── harmony.py           Ecosystem Harmony calculation
```

## Known simplifications (fine for Milestone 1, flag before extending)

- Only Timo exists. Mara, Nilo, and Eda are not yet implemented (GDD §23
  says to add them one at a time, after this loop is solid).
- The Harmony formula only includes the two conditions relevant to
  Timo/the bridge; the rest of the GDD §11 formula gets added alongside
  the systems it measures.
- No debug "reset rock to start" safeguard yet (GDD §21.2 flags this as
  needed) — if you want to replay, just restart the game.
- No sprites/tiles yet — flat colored rectangles per GDD §5.5's note that
  the behavior system should run fine before real art exists.
