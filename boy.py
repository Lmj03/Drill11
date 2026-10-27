"""Boy sprite rendering and state-driven behavior."""

from datetime import datetime
import random

import pico2d

from config import (
    ANIMATION_FPS, ASSET_DIR, AUTO_RUN_DURATION, AUTO_SPEED_MULTIPLIER,
    BASE_SCALE, BASE_SPEED, CANVAS_WIDTH,
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


class State:
    name = "STATE"

    def enter(self, boy, now):
        pass

    def exit(self, boy):
        pass

    def handle_key(self, boy, key, pressed, now):
        pass

    def update(self, boy, dt, now):
        pass


class Idle(State):
    name = "IDLE"

    def enter(self, boy, now):
        boy.is_running = False

    def handle_key(self, boy, key, pressed, now):
        if pressed and key in ("left", "right"):
            boy.change_state(Run(), now)
        elif pressed and key == "a":
            boy.change_state(AutoRun(), now)


class Run(State):
    name = "RUN"

    def enter(self, boy, now):
        boy.is_running = True

    def handle_key(self, boy, key, pressed, now):
        if pressed and key == "a":
            boy.change_state(AutoRun(), now)
        elif key in ("left", "right") and not boy.pressed_keys:
            boy.change_state(Idle(), now)

    def update(self, boy, dt, now):
        # Opposing keys cancel movement, while facing keeps the last keydown.
        if len(boy.pressed_keys) == 1:
            boy.x += boy.facing * boy.speed * dt
        half_width = boy.visible_width / 2
        boy.x = max(half_width, min(CANVAS_WIDTH - half_width, boy.x))


class AutoRun(State):
    name = "AUTO_RUN"

    def enter(self, boy, now):
        boy.is_running = True
        boy.facing = boy.choose_direction((-1, 1))
        boy.auto_started_at = now
        boy.auto_elapsed = 0.0

    def update(self, boy, dt, now):
        previous_speed = boy.speed
        boy.auto_elapsed = max(boy.auto_elapsed,
                               (now - boy.auto_started_at).total_seconds())
        if boy.auto_elapsed >= AUTO_RUN_DURATION:
            boy.change_state(Idle(), now)
            return
        progress = boy.auto_elapsed / AUTO_RUN_DURATION
        boy.speed = BASE_SPEED * (1 + (AUTO_SPEED_MULTIPLIER - 1) * progress)
        # Trapezoid integration is exact for linear acceleration.
        boy.x += boy.facing * (previous_speed + boy.speed) / 2 * dt


class Boy:
    def __init__(self, *, load_graphics=True, clock=None, choose_direction=None):
        self.clock = clock or datetime.now
        self.choose_direction = choose_direction or random.choice
        self.image = (pico2d.load_image(str(ASSET_DIR / "animation_sheet.png"))
                      if load_graphics else None)
        self.x = CANVAS_WIDTH / 2
        self.ground_y = GROUND_Y
        self.facing = 1
        self.speed = BASE_SPEED
        self.scale = BASE_SCALE
        self.animation_time = 0.0
        self.is_running = False
        self.pressed_keys = set()
        self.auto_started_at = None
        self.auto_elapsed = 0.0
        self.state = Idle()
        self.state.enter(self, self.clock())

    def change_state(self, state, now):
        self.state.exit(self)
        self.state = state
        self.animation_time = 0.0
        self.state.enter(self, now)

    def handle_key(self, key, pressed, now=None):
        if key in ("left", "right"):
            if pressed:
                if key in self.pressed_keys:
                    return  # OS key repeat must not change the last real input.
                self.pressed_keys.add(key)
                self.facing = -1 if key == "left" else 1
            else:
                self.pressed_keys.discard(key)
                if len(self.pressed_keys) == 1:
                    self.facing = -1 if "left" in self.pressed_keys else 1
        self.state.handle_key(self, key, pressed,
                              now if now is not None else self.clock())

    def update(self, dt, now=None):
        now = now if now is not None else self.clock()
        dt = max(0.0, dt)
        self.animate(dt)
        self.state.update(self, dt, now)

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
