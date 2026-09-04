"""
Renderer - reads state, decides nothing (GDD 15.3).
Flat-color rectangles stand in for pixel art per GDD 5.5 / Appendix.
"""
import pygame
import settings as s


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("consolas", 16)
        self.small_font = pygame.font.SysFont("consolas", 13)

    def draw(self, world, agents, player, harmony_value, debug=False, prompt=None, stable=False):
        self._draw_terrain(world)
        self._draw_dynamic_objects(world)
        self._draw_agents(agents)
        self._draw_player(player)
        if debug:
            self._draw_debug(world, agents, player)
        self._draw_hud(harmony_value, prompt)
        if stable:
            self._draw_stable_message()

    def _draw_terrain(self, world):
        for y in range(s.MAP_HEIGHT):
            for x in range(s.MAP_WIDTH):
                tile_id = world.grid[y][x]
                color = s.TILE_COLORS.get(tile_id, (0, 0, 0))
                rect = pygame.Rect(x * s.TILE_SIZE, y * s.TILE_SIZE, s.TILE_SIZE, s.TILE_SIZE)
                pygame.draw.rect(self.screen, color, rect)

    def _draw_dynamic_objects(self, world):
        # Bridge overrides its base tile color depending on live state.
        bridge_color = {
            "broken": s.TILE_COLORS[s.BRIDGE_BROKEN],
            "repairing": (200, 150, 60),
            "repaired": s.TILE_COLORS[s.BRIDGE_REPAIRED],
        }[world.bridge.state]
        for (x, y) in world.bridge.tiles:
            rect = pygame.Rect(x * s.TILE_SIZE, y * s.TILE_SIZE, s.TILE_SIZE, s.TILE_SIZE)
            pygame.draw.rect(self.screen, bridge_color, rect)

        if world.rock.placed:
            x, y = world.rock.position
            rect = pygame.Rect(x * s.TILE_SIZE, y * s.TILE_SIZE, s.TILE_SIZE, s.TILE_SIZE)
            pygame.draw.rect(self.screen, s.TILE_COLORS[s.ROCK_MOVABLE], rect)
            pygame.draw.rect(self.screen, (60, 50, 40), rect, 2)

        # Mara's worked plot overrides its base farm_soil color while a
        # crop is growing, same pattern as the bridge above (GDD 4.1:
        # "later states should visibly show planted and mature crops").
        crop_colors = {"planted": (150, 130, 60), "growing": (140, 170, 70), "mature": (220, 195, 40)}
        crop_color = crop_colors.get(world.farm.crop_state)
        if crop_color and world.farm.tiles:
            x, y = world.farm.tiles[0]
            rect = pygame.Rect(x * s.TILE_SIZE, y * s.TILE_SIZE, s.TILE_SIZE, s.TILE_SIZE)
            pygame.draw.rect(self.screen, crop_color, rect)

    def _draw_agents(self, agents):
        for agent in agents:
            x, y = agent.pixel_pos
            rect = pygame.Rect(x + 4, y + 4, s.TILE_SIZE - 8, s.TILE_SIZE - 8)
            pygame.draw.rect(self.screen, agent.color, rect, border_radius=4)

    def _draw_player(self, player):
        x, y = player.pixel_pos
        rect = pygame.Rect(x + 4, y + 4, s.TILE_SIZE - 8, s.TILE_SIZE - 8)
        pygame.draw.ellipse(self.screen, s.PLAYER_COLOR, rect)

    def _draw_hud(self, harmony_value, prompt):
        text = self.font.render(f"Ecosystem Harmony: {harmony_value}%", True, s.HARMONY_TEXT_COLOR)
        pad = pygame.Rect(4, 4, text.get_width() + 12, text.get_height() + 8)
        pygame.draw.rect(self.screen, (255, 255, 255), pad)
        self.screen.blit(text, (10, 8))

        if prompt:
            p = self.small_font.render(prompt, True, (255, 255, 255))
            bg = pygame.Rect(s.SCREEN_WIDTH // 2 - p.get_width() // 2 - 6, s.SCREEN_HEIGHT - 30,
                              p.get_width() + 12, p.get_height() + 6)
            pygame.draw.rect(self.screen, (20, 20, 20), bg)
            self.screen.blit(p, (bg.x + 6, bg.y + 3))

    def _draw_stable_message(self):
        """GDD 12.3: the colony has reached its stable configuration."""
        lines = ["The colony no longer needs your help.", "You understood enough to let it live.", "(R to replay)"]
        rendered = [self.font.render(line, True, (255, 255, 255)) for line in lines]
        width = max(r.get_width() for r in rendered) + 40
        height = sum(r.get_height() for r in rendered) + 30

        overlay = pygame.Surface((s.SCREEN_WIDTH, s.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        box = pygame.Rect(0, 0, width, height)
        box.center = (s.SCREEN_WIDTH // 2, s.SCREEN_HEIGHT // 2)
        pygame.draw.rect(self.screen, (25, 25, 25), box, border_radius=8)

        y = box.top + 15
        for r in rendered:
            self.screen.blit(r, (box.centerx - r.get_width() // 2, y))
            y += r.get_height()

    def _draw_debug(self, world, agents, player):
        lines = [
            f"player tile: {player.tile_pos}  facing: {player.direction}",
            f"rock: {world.rock.position} placed={world.rock.placed}",
            f"bridge: {world.bridge.state} wood={world.bridge.wood_delivered}/{3}",
            f"seeds: discovered={world.seeds.discovered}  farm: {world.farm.crop_state} "
            f"harvested={world.farm.total_harvested}  storage.food={world.storage.food}",
            f"food distributed={world.total_food_distributed}",
        ]
        for agent in agents:
            lines.append(
                f"{agent.name}: fsm={getattr(agent, 'fsm_state', '?')} "
                f"goal={agent.current_goal} action={agent.current_action} "
                f"target={agent.target} blocked={agent.blocked}"
            )
        y = 40
        for line in lines:
            surf = self.small_font.render(line, True, s.DEBUG_TEXT_COLOR)
            self.screen.blit(surf, (10, y))
            y += 16
