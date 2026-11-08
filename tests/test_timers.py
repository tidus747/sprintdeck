import test_state
import unittest


class TimerTests(unittest.TestCase):
    setUp = test_state.StateTests.setUp
    act = test_state.StateTests.act
    def timer(self, operation, **values):
        return self.act("timer", timer="individual", operation=operation, **values)["timers"]["individual"]

    def test_start_pause_resume_and_reset(self):
        self.assertEqual(self.timer("start")["deadline"], 1300)
        self.now += 30
        self.assertEqual(self.timer("start")["deadline"], 1300)
        self.assertEqual(self.timer("pause")["seconds_left"], 270)
        self.now += 100
        self.assertEqual(self.timer("pause")["seconds_left"], 270)
        self.assertEqual(self.timer("resume")["deadline"], 1400)
        self.now += 50
        self.assertEqual(self.timer("pause")["seconds_left"], 220)
        reset = self.timer("reset", duration=120)
        self.assertEqual(reset["seconds_left"], 120)
        self.assertIsNone(reset["deadline"])

    def test_expiration_does_not_go_negative_or_write_during_reads(self):
        self.timer("start")
        before = self.path.read_bytes()
        self.now = 1500
        self.assertEqual(self.store.snapshot()["timers"]["individual"]["seconds_left"], 0)
        self.assertEqual(self.path.read_bytes(), before)

    def test_member_selection_does_not_reset_timer(self):
        self.timer("start")
        self.now += 50
        value = self.act("select_member", member_id=self.second)
        self.assertEqual(value["timers"]["individual"]["seconds_left"], 250)

    def test_restart_running_and_paused(self):
        from sprintdeck.state import Store
        self.timer("start")
        self.now += 100
        restored = Store(self.path, clock=lambda: self.now)
        self.assertEqual(restored.snapshot()["timers"]["individual"]["seconds_left"], 200)
        self.timer("pause")
        self.now += 2000
        restored = Store(self.path, clock=lambda: self.now)
        self.assertEqual(restored.snapshot()["timers"]["individual"]["seconds_left"], 200)

    def test_restart_after_expiration(self):
        from sprintdeck.state import Store
        self.timer("start")
        self.now += 1000
        self.assertEqual(Store(self.path, clock=lambda: self.now).snapshot()["timers"]["individual"]["seconds_left"], 0)
