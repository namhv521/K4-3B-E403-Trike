import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from player import PlaybackClock, is_finished


class PlaybackClockTests(unittest.TestCase):
    def test_play_pause_and_seek(self):
        clock = PlaybackClock(duration=90, position=10)
        clock.play(now=100)
        self.assertEqual(13, clock.current(now=103))
        clock.pause(now=105)
        self.assertEqual(15, clock.current(now=200))
        clock.seek(30, now=200)
        self.assertEqual(30, clock.current(now=200))
        clock.play(now=200)
        self.assertEqual(32, clock.current(now=202))

    def test_clock_clamps_to_duration(self):
        clock = PlaybackClock(duration=40, position=39)
        clock.play(now=0)
        self.assertEqual(40, clock.current(now=5))

    def test_position_at_duration_finishes_session(self):
        self.assertTrue(is_finished(80.0, 80.0))
        self.assertFalse(is_finished(79.9, 80.0))

    def test_answer_keys_are_ignored_during_correct_feedback(self):
        from player import InteractivePlayer

        player = InteractivePlayer.__new__(InteractivePlayer)
        player.pygame = SimpleNamespace(
            K_ESCAPE=1, K_r=2, K_0=3, K_1=4, K_KP0=5, K_KP1=6,
            K_a=7, K_b=8, K_c=9, K_d=10, K_SPACE=11,
        )
        player.completed = False
        player.correct_feedback_until = 1.0
        player.session = SimpleNamespace(
            active_checkpoint_id="cp1",
            feedback_until=None,
            submit_answer=Mock(),
        )
        self.assertTrue(player._handle_key(player.pygame.K_a))
        player.session.submit_answer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
