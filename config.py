"""Shared dimensions and tuning values for the pico2d demo."""

from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parent
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
GROUND_Y = 52

# An 800 px canvas takes roughly 3.3 seconds to cross at the normal speed.
BASE_SPEED = 240.0  # pixels / second
BASE_SCALE = 1.0
AUTO_RUN_DURATION = 5.0
AUTO_SPEED_MULTIPLIER = 3.0
AUTO_SCALE_MULTIPLIER = 2.0

FRAME_WIDTH = 100
FRAME_HEIGHT = 100
FRAME_COUNT = 8
ANIMATION_FPS = 10.0
TARGET_FPS = 60
