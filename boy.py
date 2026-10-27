"""Boy sprite rendering and state-driven behavior."""

import pico2d

from config import (
    ANIMATION_FPS, ASSET_DIR, BASE_SCALE, BASE_SPEED, CANVAS_WIDTH,
    FRAME_COUNT, FRAME_HEIGHT, FRAME_WIDTH, GROUND_Y,
)

# Alpha bounds in each 100x100 source cell: left, top, right, bottom.
# Use visible pixels rather than transparent padding for contact and walls.
SPRITE_BOUNDS = (
    ((31,10,66,88), (31,9,66,88), (33,11,66,88), (36,13,68,88),
     (34,11,67,88), (32,10,66,88), (34,11,68,88), (34,11,68,88)),
    ((36,10,71,88), (36,9,71,88), (36,11,69,88), (34,13,66,88),
     (35,11,68,88), (36,10,70,88), (34,11,68,88), (34,11,68,88)),
    ((28,21,80,86), (18,20,79,82), (31,21,79,88), (36,23,74,88),
     (31,21,74,89), (22,20,79,83), (31,21,74,88), (34,23,74,89)),
    ((22,21,74,86), (23,20,84,82), (24,21,72,88), (30,23,68,88),
     (29,21,72,89), (24,20,81,83), (30,21,73,88), (28,23,68,89)),
)


class Boy:
    def __init__(self, *, load_graphics=True):
        self.image = (pico2d.load_image(str(ASSET_DIR / "animation_sheet.png"))
                      if load_graphics else None)
        self.x = CANVAS_WIDTH / 2
        self.ground_y = GROUND_Y
        self.facing = 1
        self.speed = BASE_SPEED
        self.scale = BASE_SCALE
        self.animation_time = 0.0
        self.is_running = False

    @property
    def frame(self):
        return int(self.animation_time * ANIMATION_FPS) % FRAME_COUNT

    @property
    def sprite_row(self):
        return (2 if self.is_running else 0) + (1 if self.facing < 0 else 0)

    @property
    def bounds(self):
        return SPRITE_BOUNDS[self.sprite_row][self.frame]

    @property
    def visible_width(self):
        left, _, right, _ = self.bounds
        return (right - left) * self.scale

    def animate(self, dt):
        self.animation_time += dt

    def draw(self):
        if self.image is None:
            return
        left, _, right, bottom = self.bounds
        # x is the visible sprite's center; y anchors its lowest opaque pixel.
        center_x = self.x + (FRAME_WIDTH / 2 - (left + right) / 2) * self.scale
        center_y = self.ground_y + (bottom - FRAME_HEIGHT / 2) * self.scale
        self.image.clip_draw(
            self.frame * FRAME_WIDTH,
            self.image.h - (self.sprite_row + 1) * FRAME_HEIGHT,
            FRAME_WIDTH, FRAME_HEIGHT, center_x, center_y,
            FRAME_WIDTH * self.scale, FRAME_HEIGHT * self.scale,
        )
