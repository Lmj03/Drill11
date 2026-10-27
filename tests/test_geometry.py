"""Wall reflection, frame timing, and actual sprite contact checks."""

from datetime import datetime, timedelta
import unittest

from PIL import Image

from boy import AutoRun, Boy, SPRITE_BOUNDS
from config import ASSET_DIR, BASE_SPEED, CANVAS_WIDTH, GROUND_Y


class RecordingImage:
    h = 402

    def clip_draw(self, *args):
        self.args = args


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 27, 12)
        self.boy = Boy(load_graphics=False, clock=lambda: self.now,
                       choose_direction=lambda _: 1)
        self.boy.handle_key("a", True, self.now)

    def test_both_walls_reflect_without_resetting_growth(self):
        self.now += timedelta(seconds=2)
        self.boy.update(2, self.now)
        started = self.boy.auto_started_at
        for edge, expected_direction in ((-10, 1), (CANVAS_WIDTH + 10, -1)):
            with self.subTest(edge=edge):
                self.boy.x = edge
                self.boy.update(0, self.now)
                self.assertIsInstance(self.boy.state, AutoRun)
                self.assertEqual(self.boy.facing, expected_direction)
                half = self.boy.visible_width / 2
                self.assertGreaterEqual(self.boy.x, half)
                self.assertLessEqual(self.boy.x, CANVAS_WIDTH - half)
                self.assertEqual(self.boy.auto_elapsed, 2)
                self.assertEqual(self.boy.auto_started_at, started)
                self.assertAlmostEqual(self.boy.scale, 1.4)
                self.assertAlmostEqual(self.boy.speed, BASE_SPEED * 1.8)

    def test_slow_frame_can_cross_multiple_walls_safely(self):
        self.boy.update(4.5, self.now + timedelta(seconds=4.5))
        half = self.boy.visible_width / 2
        self.assertGreaterEqual(self.boy.x, half)
        self.assertLessEqual(self.boy.x, CANVAS_WIDTH - half)
        self.assertIsInstance(self.boy.state, AutoRun)

    def test_randomized_wall_entry_points_and_frame_intervals(self):
        # Covers gradual growth, changing sprite widths, and repeated bounces.
        for fps in (15, 30, 60, 144):
            boy = Boy(load_graphics=False, clock=lambda: self.now,
                      choose_direction=lambda _: -1)
            boy.handle_key("a", True, self.now)
            previous = self.now
            for frame in range(1, fps * 5):
                now = self.now + timedelta(seconds=frame / fps)
                boy.update((now - previous).total_seconds(), now)
                previous = now
                half = boy.visible_width / 2
                self.assertGreaterEqual(boy.x + 1e-8, half)
                self.assertLessEqual(boy.x - 1e-8, CANVAS_WIDTH - half)

    def test_acceleration_is_consistent_across_frame_rates(self):
        for fps in (30, 60, 144):
            boy = Boy(load_graphics=False, clock=lambda: self.now,
                      choose_direction=lambda _: 1)
            boy.x = 200
            boy.handle_key("a", True, self.now)
            previous = self.now
            for frame in range(1, fps // 2 + 1):
                now = self.now + timedelta(seconds=frame / fps)
                boy.update((now - previous).total_seconds(), now)
                previous = now
            self.assertAlmostEqual(boy.x, 332.0, places=6)
            self.assertAlmostEqual(boy.speed, 288.0)
            self.assertAlmostEqual(boy.scale, 1.1)

    def test_recorded_bounds_match_every_png_frame(self):
        with Image.open(ASSET_DIR / "animation_sheet.png") as sheet:
            sheet = sheet.convert("RGBA")
            for row in range(4):
                for frame in range(8):
                    actual = sheet.crop((frame * 100, row * 100,
                                         frame * 100 + 100, row * 100 + 100)).getbbox()
                    self.assertEqual(actual, SPRITE_BOUNDS[row][frame])

    def test_visible_feet_and_horizontal_center_stay_anchored(self):
        image = RecordingImage()
        self.boy.image = image
        for running in (False, True):
            self.boy.is_running = running
            for facing in (-1, 1):
                self.boy.facing = facing
                for frame in range(8):
                    self.boy.animation_time = (frame + 0.1) / 10
                    for scale in (1, 1.3, 2):
                        self.boy.scale = scale
                        self.boy.draw()
                        _, _, _, _, cx, cy, w, h = image.args
                        left, _, right, bottom = self.boy.bounds
                        visible_bottom = cy + h / 2 - bottom * scale
                        visible_center = cx - w / 2 + (left + right) / 2 * scale
                        self.assertAlmostEqual(visible_bottom, GROUND_Y)
                        self.assertAlmostEqual(visible_center, self.boy.x)

    def test_opposing_keys_do_not_shift_position_at_wall(self):
        self.boy.handle_key("left", True, self.now)
        self.boy.x = self.boy.visible_width / 2
        self.boy.handle_key("right", True, self.now)
        x = self.boy.x
        self.boy.update(0.1, self.now + timedelta(seconds=0.1))
        self.assertEqual(self.boy.x, x)

    def test_manual_run_stays_within_canvas(self):
        for direction in ("left", "right"):
            self.boy.release_keys(self.now)
            self.boy.handle_key(direction, True, self.now)
            self.boy.update(100, self.now)
            half = self.boy.visible_width / 2
            self.assertGreaterEqual(self.boy.x, half)
            self.assertLessEqual(self.boy.x, CANVAS_WIDTH - half)


if __name__ == "__main__":
    unittest.main()
