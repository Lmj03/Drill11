"""State acceptance tests with a controlled datetime clock; no window needed."""

from datetime import datetime, timedelta
from types import SimpleNamespace
import unittest

import pico2d

from boy import AutoRun, Boy, Idle, Run
from config import BASE_SCALE, BASE_SPEED
from main import process_events


class StateTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 27, 12)
        self.choices = []

        def choose(options):
            self.choices.append(options)
            return -1 if len(self.choices) % 2 else 1

        self.boy = Boy(load_graphics=False, clock=lambda: self.now,
                       choose_direction=choose)

    def key(self, key, pressed=True):
        self.boy.handle_key(key, pressed, self.now)

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)
        self.boy.update(seconds, self.now)

    def assert_base(self):
        self.assertEqual(self.boy.speed, BASE_SPEED)
        self.assertEqual(self.boy.scale, BASE_SCALE)
        self.assertIsNone(self.boy.auto_started_at)
        self.assertEqual(self.boy.auto_elapsed, 0)

    def test_initial_idle(self):
        self.assertIsInstance(self.boy.state, Idle)
        x = self.boy.x
        self.advance(0.25)
        self.assertEqual(self.boy.x, x)
        self.assert_base()

    def test_manual_run_and_release(self):
        for key, direction in (("left", -1), ("right", 1)):
            with self.subTest(key=key):
                x = self.boy.x
                self.key(key)
                self.assertIsInstance(self.boy.state, Run)
                self.advance(0.1)
                self.assertAlmostEqual(self.boy.x, x + direction * BASE_SPEED * 0.1)
                self.key(key, False)
                self.assertIsInstance(self.boy.state, Idle)

    def test_opposing_keys_face_last_and_stop_in_both_orders(self):
        for first, second, facing in (("left", "right", 1), ("right", "left", -1)):
            with self.subTest(first=first):
                self.key(first)
                self.key(second)
                x = self.boy.x
                self.advance(0.1)
                self.assertEqual(self.boy.x, x)
                self.assertEqual(self.boy.facing, facing)
                self.key(first)  # Key repeat does not become the latest press.
                self.assertEqual(self.boy.facing, facing)
                self.key(second, False)
                self.advance(0.1)
                self.assertNotEqual(self.boy.x, x)
                self.key(first, False)

    def test_random_direction_is_chosen_once_per_entry(self):
        for expected in (-1, 1):
            self.key("a")
            self.assertIsInstance(self.boy.state, AutoRun)
            self.assertEqual(self.boy.facing, expected)
            calls = len(self.choices)
            self.advance(0.1)
            self.assertEqual(len(self.choices), calls)
            self.assertEqual(self.boy.facing, expected)
            self.key("right")
            self.key("right", False)
        self.assertEqual(self.choices, [(-1, 1), (-1, 1)])

    def test_can_enter_auto_from_run(self):
        self.key("left")
        self.key("a")
        self.assertIsInstance(self.boy.state, AutoRun)

    def test_linear_speed_and_scale(self):
        self.key("a")
        for elapsed in (1, 2, 3, 4):
            self.advance(1)
            self.assertAlmostEqual(self.boy.speed, BASE_SPEED * (1 + 2 * elapsed / 5))
            self.assertAlmostEqual(self.boy.scale, 1 + elapsed / 5)

    def test_timeout_exactly_five_seconds_restores_everything(self):
        self.key("a")
        self.advance(4.999)
        self.assertIsInstance(self.boy.state, AutoRun)
        self.advance(0.001)
        self.assertIsInstance(self.boy.state, Idle)
        self.assert_base()

    def test_left_and_right_cancel_and_restore(self):
        for key, direction in (("left", -1), ("right", 1)):
            with self.subTest(key=key):
                self.key("a")
                self.advance(1)
                self.key(key)
                self.assertIsInstance(self.boy.state, Run)
                self.assertEqual(self.boy.facing, direction)
                self.assert_base()
                self.key(key, False)

    def test_auto_cancel_with_opposing_keys_does_not_move(self):
        self.key("left")
        self.key("a")
        self.key("right")
        self.assertIsInstance(self.boy.state, Run)
        self.assertEqual(self.boy.facing, 1)
        x = self.boy.x
        self.advance(0.1)
        self.assertEqual(self.boy.x, x)
        self.assert_base()

    def test_other_keys_and_repeated_a_preserve_original_timer(self):
        self.key("a")
        started = self.boy.auto_started_at
        self.advance(2)
        speed, scale = self.boy.speed, self.boy.scale
        for key in ("a", "other", "space", "escape"):
            self.key(key)
            self.key(key, False)
            self.assertIsInstance(self.boy.state, AutoRun)
            self.assertEqual(self.boy.auto_started_at, started)
            self.assertEqual((self.boy.speed, self.boy.scale), (speed, scale))
        self.advance(3)
        self.assertIsInstance(self.boy.state, Idle)

    def test_arrow_wins_over_timeout_in_same_frame(self):
        self.key("a")
        self.now += timedelta(seconds=5)
        events = [SimpleNamespace(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_RIGHT)]
        self.assertTrue(process_events(self.boy, events, self.now))
        self.boy.update(5, self.now)
        self.assertIsInstance(self.boy.state, Run)
        self.assertEqual(self.boy.facing, 1)
        self.assert_base()

    def test_reentry_clears_previous_growth(self):
        self.key("a")
        self.advance(3)
        self.key("left")
        self.key("left", False)
        self.key("a")
        self.assertEqual(self.boy.auto_elapsed, 0)
        self.assertEqual(self.boy.speed, BASE_SPEED)
        self.assertEqual(self.boy.scale, BASE_SCALE)
        self.assertEqual(self.boy.auto_started_at, self.now)

    def test_releasing_preexisting_key_does_not_change_auto_direction(self):
        self.key("left")
        self.key("right")
        self.key("a")
        self.assertEqual(self.boy.facing, -1)
        self.key("left", False)
        self.assertEqual(self.boy.facing, -1)
        self.assertIsInstance(self.boy.state, AutoRun)

    def test_focus_loss_stops_run_but_preserves_auto(self):
        self.key("left")
        self.boy.release_keys(self.now)
        self.assertIsInstance(self.boy.state, Idle)
        self.assertFalse(self.boy.pressed_keys)
        self.key("a")
        self.advance(1)
        started = self.boy.auto_started_at
        self.boy.release_keys(self.now)
        self.assertIsInstance(self.boy.state, AutoRun)
        self.assertEqual(self.boy.auto_started_at, started)

    def test_close_event_stops_event_processing(self):
        self.assertFalse(process_events(self.boy, [SimpleNamespace(type=pico2d.SDL_QUIT)], self.now))


if __name__ == "__main__":
    unittest.main()
