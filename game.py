import pygame
import settings as s
from world.world import World
from entities.player import Player
from entities.timo import TimoAgent
from entities.nilo import NiloAgent
from entities.mara import MaraAgent
from entities.eda import EdaAgent
from renderer import Renderer
from systems.harmony import compute_harmony, StableStateTracker


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((s.SCREEN_WIDTH, s.SCREEN_HEIGHT))
        pygame.display.set_caption("Little Colony - Milestone 1")
        self.clock = pygame.time.Clock()
        self.running = True
        self.debug = False
        self.renderer = Renderer(self.screen)
        self._new_level()

    def _new_level(self):
        """(Re)build the whole simulation - used at startup and on Replay."""
        self.world = World()
        self.player = Player((2, 9))
        self.timo = TimoAgent((6, 9), self.world)
        self.nilo = NiloAgent((8, 5), self.world)
        self.mara = MaraAgent((2, 2), self.world)
        self.eda = EdaAgent((8, 3), self.world)
        self.agents = [self.timo, self.nilo, self.mara, self.eda]
        self.stable_tracker = StableStateTracker(hold_time=3.0)
        self.harmony = compute_harmony(self.world)

    def run(self):
        while self.running:
            dt = self.clock.tick(s.TARGET_FPS) / 1000.0
            self._process_input(dt)
            self._update(dt)
            self._draw()
        pygame.quit()

    # ---- Update order (GDD 15.2) --------------------------------------

    def _process_input(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_F1:
                    self.debug = not self.debug
                elif event.key in (pygame.K_e, pygame.K_SPACE):
                    self._try_interact()
                elif event.key == pygame.K_r and self.stable_tracker.is_stable:
                    self._new_level()
                    return

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.world)

    def _try_interact(self):
        """Player action: move the rock to the tile they're facing."""
        target = self.player.facing_tile()
        if self.world.rock.placed and self._adjacent(self.player.tile_pos, self.world.rock.position):
            moved = self.world.try_move_rock(target if target != self.world.rock.position else self._first_free_adjacent())
            return moved
        return False

    def _adjacent(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def _first_free_adjacent(self):
        rx, ry = self.world.rock.position
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            candidate = (rx + dx, ry + dy)
            if self.world.is_walkable_ignoring_rock(*candidate) and candidate not in self.world.bridge.tiles:
                return candidate
        return self.world.rock.position

    def _update(self, dt):
        self.world.update(dt)
        for agent in self.agents:
            agent.update(self.world, dt)
        self.world.pop_events()  # Milestone 1: drained, not yet consumed by an ObservationSystem.

        self.harmony = compute_harmony(self.world)
        self.stable_tracker.update(dt, self.harmony)

    def _draw(self):
        prompt = None
        if self.world.rock.placed and self._adjacent(self.player.tile_pos, self.world.rock.position):
            prompt = "E - Move rock"
        self.screen.fill((0, 0, 0))
        self.renderer.draw(
            self.world, self.agents, self.player, self.harmony, debug=self.debug, prompt=prompt,
            stable=self.stable_tracker.is_stable,
        )
        pygame.display.flip()
