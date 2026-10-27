"""Run with: python main.py"""

from datetime import datetime
import os
from pathlib import Path

import pico2d
from pico2d import pico2d as canvas

from boy import Boy
from config import AUTO_RUN_DURATION, CANVAS_HEIGHT, CANVAS_WIDTH, TARGET_FPS
from grass import Grass

KEY_NAMES = {
    pico2d.SDLK_LEFT: "left",
    pico2d.SDLK_RIGHT: "right",
    pico2d.SDLK_a: "a",
}


def process_events(boy, events, now):
    """Process all input before update, so arrows win over time expiration."""
    for event in events:
        if event.type == pico2d.SDL_QUIT:
            return False
        if event.type in (pico2d.SDL_KEYDOWN, pico2d.SDL_KEYUP):
            boy.handle_key(KEY_NAMES.get(event.key, "other"),
                           event.type == pico2d.SDL_KEYDOWN, now)
    return True


def load_hud_font():
    candidates = (
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "consola.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Menlo.ttc"),
    )
    for path in candidates:
        if path.is_file():
            return pico2d.load_font(str(path), 18)
    return None


def draw_scene(grass, boy, font=None):
    pico2d.clear_canvas()
    grass.draw()
    boy.draw()
    remaining = max(0.0, AUTO_RUN_DURATION - boy.auto_elapsed)
    status = (f"{boy.state.name} | speed {boy.speed:.0f} px/s | "
              f"scale {boy.scale:.2f}x")
    if boy.state.name == "AUTO_RUN":
        status += f" | {remaining:.1f}s left"
    if font is not None:
        font.draw(24, CANVAS_HEIGHT - 32, "AUTO RUN / pico2d", (35, 45, 65))
        font.draw(24, CANVAS_HEIGHT - 62, "A: auto run   Left/Right: move", (50, 60, 75))
        font.draw(24, CANVAS_HEIGHT - 92, status, (40, 55, 85))
    pico2d.SDL_SetWindowTitle(canvas.window, ("AutoRun | " + status).encode())


def open_game_canvas():
    pico2d.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    # pico2d 1.5.1 checks `is None`, but SDL can return a null pointer object.
    # Ensure software rendering is available when accelerated SDL is absent.
    if not canvas.renderer and canvas.window:
        canvas.renderer = pico2d.SDL_CreateRenderer(
            canvas.window, -1, pico2d.SDL_RENDERER_SOFTWARE)
    if not canvas.window or not canvas.renderer:
        error = pico2d.SDL_GetError().decode("utf-8", errors="replace")
        pico2d.close_canvas()
        raise RuntimeError(f"pico2d could not create an SDL canvas: {error}")
    pico2d.hide_lattice()


def main(*, max_frames=None):
    open_game_canvas()
    try:
        grass = Grass()
        boy = Boy()
        font = load_hud_font()
        previous = datetime.now()
        frames = 0
        while max_frames is None or frames < max_frames:
            now = datetime.now()
            dt = max(0.0, (now - previous).total_seconds())
            previous = now
            if not process_events(boy, pico2d.get_events(), now):
                break
            if not (pico2d.SDL_GetWindowFlags(canvas.window)
                    & pico2d.SDL_WINDOW_INPUT_FOCUS):
                boy.release_keys(now)
            boy.update(dt, now)
            draw_scene(grass, boy, font)
            pico2d.update_canvas()
            frames += 1
            spent = (datetime.now() - now).total_seconds()
            pico2d.delay(max(0.0, 1.0 / TARGET_FPS - spent))
    finally:
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
