"""Player-controlled visitor/facilitator (GDD section 6)."""
import settings as s


class Player:
    def __init__(self, tile_pos):
        self.pixel_pos = [tile_pos[0] * s.TILE_SIZE, tile_pos[1] * s.TILE_SIZE]
        self.direction = "down"
        self.carrying = None  # e.g. a resource the player picked up

    @property
    def tile_pos(self):
        return (
            int((self.pixel_pos[0] + s.TILE_SIZE / 2) // s.TILE_SIZE),
            int((self.pixel_pos[1] + s.TILE_SIZE / 2) // s.TILE_SIZE),
        )

    def facing_tile(self):
        tx, ty = self.tile_pos
        return {
            "up": (tx, ty - 1), "down": (tx, ty + 1),
            "left": (tx - 1, ty), "right": (tx + 1, ty),
        }[self.direction]

    def update(self, dt, keys, world):
        import pygame
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1; self.direction = "left"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1; self.direction = "right"
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1; self.direction = "up"
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1; self.direction = "down"

        if dx == 0 and dy == 0:
            return

        step = s.PLAYER_SPEED * dt
        new_x = self.pixel_pos[0] + dx * step
        new_y = self.pixel_pos[1] + dy * step

        if self._can_stand_at(new_x, self.pixel_pos[1], world):
            self.pixel_pos[0] = new_x
        if self._can_stand_at(self.pixel_pos[0], new_y, world):
            self.pixel_pos[1] = new_y

    def _can_stand_at(self, px, py, world):
        # Check all four corners of the player's tile-sized bounding box.
        margin = 4
        corners = [
            (px + margin, py + margin),
            (px + s.TILE_SIZE - margin, py + margin),
            (px + margin, py + s.TILE_SIZE - margin),
            (px + s.TILE_SIZE - margin, py + s.TILE_SIZE - margin),
        ]
        for cx, cy in corners:
            tx, ty = int(cx // s.TILE_SIZE), int(cy // s.TILE_SIZE)
            if not world.is_walkable(tx, ty):
                return False
        return True
