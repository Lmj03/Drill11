"""The grass image is loaded once, after the canvas opens."""

import pico2d

from config import ASSET_DIR, CANVAS_WIDTH


class Grass:
    def __init__(self):
        self.image = pico2d.load_image(str(ASSET_DIR / "grass.png"))

    def draw(self):
        self.image.draw(CANVAS_WIDTH / 2, self.image.h / 2,
                        CANVAS_WIDTH + 2, self.image.h)
