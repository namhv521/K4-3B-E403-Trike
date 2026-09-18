import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import Session


def lesson():
    options = [
        {"id": "A", "text": "Đúng", "is_correct": True, "misconception": None},
        {"id": "B", "text": "Sai B", "is_correct": False, "misconception": {"id": "scope", "label": "Nhầm phạm vi"}},
        {"id": "C", "text": "Sai C", "is_correct": False, "misconception": {"id": "example", "label": "Nhầm ví dụ"}},
        {"id": "D", "text": "Sai D", "is_correct": False, "misconception": {"id": "term", "label": "Nhầm thuật ngữ"}},
    ]
    return {
        "duration_seconds": 70,
        "checkpoints": [
            {"id": "cp1", "time": 20, "concept": "AI", "question": "AI là gì?", "explanation": "AI là lĩnh vực rộng.", "options": options},
            {"id": "cp2", "time": 45, "concept": "ML", "question": "ML thuộc đâu?", "explanation": "ML thuộc AI.", "options": options},
        ],
    }


class SessionTests(unittest.TestCase):
    def test_correct_answer_seeks_ten_seconds_and_unlocks_next_checkpoint(self):
        session = Session(lesson(), "s1", started_at=0)
        session.open_checkpoint("cp1", now=10)
        attempt = session.submit_answer("A", now=12)
        self.assertTrue(attempt["is_correct"])
        self.assertEqual({"type": "seek", "time": 30, "autoplay": True}, session.next_action)
        self.assertEqual(45, session.unlocked_through)
        self.assertEqual(5.0, session.summary()["score"])

    def test_wrong_answer_waits_five_seconds_and_logs_misconception(self):
        session = Session(lesson(), "s2", started_at=0)
        session.open_checkpoint("cp1", now=10)
        attempt = session.submit_answer("B", now=12)
        self.assertEqual(17, session.feedback_until)
        self.assertEqual("scope", attempt["misconception_id"])
        with self.assertRaisesRegex(ValueError, "5 seconds"):
            session.choose_recovery("1", now=16.9)

    def test_zero_restarts_and_one_skips_to_next_checkpoint(self):
        restart = Session(lesson(), "s3", started_at=0)
        restart.open_checkpoint("cp1", now=10)
        restart.submit_answer("B", now=12)
        restart.choose_recovery("0", now=17)
        self.assertEqual(0, restart.next_action["time"])

        skip = Session(lesson(), "s4", started_at=0)
        skip.open_checkpoint("cp1", now=10)
        skip.submit_answer("B", now=12)
        skip.choose_recovery("1", now=17)
        self.assertEqual(45, skip.next_action["time"])

    def test_restart_replays_earlier_checkpoints_without_erasing_attempt_history(self):
        session = Session(lesson(), "s7", started_at=0)
        session.open_checkpoint("cp1", now=10)
        session.submit_answer("A", now=11)
        session.active_checkpoint_id = None
        session.open_checkpoint("cp2", now=20)
        session.submit_answer("B", now=21)
        session.choose_recovery("0", now=26)
        self.assertEqual(set(), session.completed)
        self.assertEqual(20, session.unlocked_through)
        self.assertEqual("cp1", session.due_checkpoint(20.8)["id"])
        self.assertEqual(2, session.summary()["total_attempts"])

    def test_later_correct_attempt_is_logged_without_restoring_score(self):
        session = Session(lesson(), "s5", started_at=0)
        session.open_checkpoint("cp1", now=10)
        session.submit_answer("B", now=12)
        session.submit_answer("A", now=20)
        report = session.summary()
        self.assertEqual(0.0, report["score"])
        self.assertEqual(2, report["total_attempts"])
        self.assertEqual(1, report["corrected_after_review"])

    def test_due_checkpoint_ignores_completed_items(self):
        session = Session(lesson(), "s6", started_at=0)
        self.assertEqual("cp1", session.due_checkpoint(20.2)["id"])
        session.completed.add("cp1")
        self.assertIsNone(session.due_checkpoint(20.2))

    def test_due_checkpoint_is_not_missed_by_a_slow_render_frame(self):
        session = Session(lesson(), "s8", started_at=0)
        self.assertEqual("cp1", session.due_checkpoint(22.0)["id"])


if __name__ == "__main__":
    unittest.main()
