"""Exercise real SDL rendering and input without opening a desktop window."""

import ctypes
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageChops
import pico2d
from pico2d import pico2d as canvas
import sdl2

from boy import AutoRun, Boy, Idle, Run
from config import BASE_SCALE, BASE_SPEED, CANVAS_HEIGHT, CANVAS_WIDTH
from grass import Grass
from main import draw_scene, load_hud_font, main, open_game_canvas, process_events


def capture():
    pixels = ctypes.create_string_buffer(CANVAS_WIDTH * CANVAS_HEIGHT * 4)
    result = sdl2.SDL_RenderReadPixels(
        canvas.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32,
        pixels, CANVAS_WIDTH * 4,
    )
    if result != 0:
        raise RuntimeError(sdl2.SDL_GetError().decode())
    return Image.frombytes("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), pixels.raw).convert("RGB")


def send_key(boy, key, now, pressed=True):
    event = sdl2.SDL_Event()
    event.type = sdl2.SDL_KEYDOWN if pressed else sdl2.SDL_KEYUP
    event.key.type = event.type
    event.key.state = sdl2.SDL_PRESSED if pressed else sdl2.SDL_RELEASED
    event.key.repeat = 0
    event.key.keysym.sym = key
    if sdl2.SDL_PushEvent(ctypes.byref(event)) < 0:
        raise RuntimeError(sdl2.SDL_GetError().decode())
    assert process_events(boy, pico2d.get_events(), now)


def run():
    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    # Real application startup, image/font loading, loop, and shutdown.
    main(max_frames=3)
    open_game_canvas()
    report = {}
    try:
        assert canvas.renderer
        now = datetime(2026, 10, 27, 12)
        boy = Boy(clock=lambda: now, choose_direction=lambda _: 1)
        grass = Grass()
        font = load_hud_font()

        def snapshot(name):
            pico2d.clear_canvas()
            boy.draw()
            image = capture()
            background = Image.new("RGB", image.size, (200, 200, 210))
            bounds = ImageChops.difference(image, background).getbbox()
            assert bounds is not None, f"No sprite pixels rendered: {name}"
            report[name] = {
                "state": boy.state.name,
                "speed": boy.speed,
                "scale": boy.scale,
                "sprite_bounds": bounds,
            }
            draw_scene(grass, boy, font)
            capture().save(output / f"{name}.png")
            pico2d.update_canvas()
            return bounds

        idle = snapshot("01_idle")
        send_key(boy, pico2d.SDLK_LEFT, now)
        now += timedelta(seconds=0.1)
        boy.update(0.1, now)
        assert isinstance(boy.state, Run)
        assert boy.x < CANVAS_WIDTH / 2
        snapshot("02_run_left")
        send_key(boy, pico2d.SDLK_RIGHT, now)
        x = boy.x
        now += timedelta(seconds=0.1)
        boy.update(0.1, now)
        assert boy.x == x and boy.facing == 1
        snapshot("03_opposing_keys")
        send_key(boy, pico2d.SDLK_LEFT, now, False)
        send_key(boy, pico2d.SDLK_RIGHT, now, False)
        send_key(boy, pico2d.SDLK_a, now)
        started = now
        now = started + timedelta(seconds=4)
        boy.update(4, now)
        assert isinstance(boy.state, AutoRun)
        enlarged = snapshot("04_auto_run")
        assert enlarged[3] == idle[3], (idle, enlarged)
        assert enlarged[3] - enlarged[1] > idle[3] - idle[1]
        assert enlarged[2] - enlarged[0] > idle[2] - idle[0]
        send_key(boy, pico2d.SDLK_a, now)
        send_key(boy, pico2d.SDLK_SPACE, now)
        assert boy.auto_started_at == started
        now = started + timedelta(seconds=5)
        boy.update(1, now)
        assert isinstance(boy.state, Idle)
        assert (boy.speed, boy.scale) == (BASE_SPEED, BASE_SCALE)
        snapshot("05_timeout_restored")
        send_key(boy, pico2d.SDLK_a, now)
        now += timedelta(seconds=5)
        send_key(boy, pico2d.SDLK_RIGHT, now)
        boy.update(0, now)
        assert isinstance(boy.state, Run)
        snapshot("06_arrow_priority")
        quit_event = sdl2.SDL_Event()
        quit_event.type = sdl2.SDL_QUIT
        assert sdl2.SDL_PushEvent(ctypes.byref(quit_event)) == 1
        assert not process_events(boy, pico2d.get_events(), now)
        report["result"] = "PASS: real SDL startup, input, rendering, contact, timeout and quit"
    finally:
        pico2d.close_canvas()
    (output / "smoke_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
