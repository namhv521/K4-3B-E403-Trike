import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lesson_schema import checkpoint_score, validate_lesson


def lesson():
    return {
        "version": 1,
        "title": "Bản đồ AI",
        "duration_seconds": 70,
        "narration": "Nội dung ôn tập.",
        "scenes": [
            {"start": 0, "end": 70, "title": "AI", "body": "Khái niệm", "source_refs": ["slide:1"]}
        ],
        "checkpoints": [
            {
                "id": "cp1",
                "time": 20,
                "concept": "AI",
                "question": "AI là gì?",
                "explanation": "AI là một lĩnh vực rộng.",
                "source_refs": ["slide:1"],
                "options": [
                    {"id": "A", "text": "Một lĩnh vực", "is_correct": True, "misconception": None},
                    {"id": "B", "text": "Một ứng dụng", "is_correct": False, "misconception": {"id": "app", "label": "Nhầm lĩnh vực với ứng dụng"}},
                    {"id": "C", "text": "Một dữ liệu", "is_correct": False, "misconception": {"id": "data", "label": "Nhầm AI với dữ liệu"}},
                    {"id": "D", "text": "Một thiết bị", "is_correct": False, "misconception": {"id": "device", "label": "Nhầm AI với thiết bị"}},
                ],
            },
            {
                "id": "cp2",
                "time": 40,
                "concept": "ML",
                "question": "ML thuộc đâu?",
                "explanation": "ML là một cách làm trong AI.",
                "source_refs": ["slide:2"],
                "options": [
                    {"id": "A", "text": "AI", "is_correct": True, "misconception": None},
                    {"id": "B", "text": "Video", "is_correct": False, "misconception": {"id": "video", "label": "Nhầm với phương tiện"}},
                    {"id": "C", "text": "Âm thanh", "is_correct": False, "misconception": {"id": "audio", "label": "Nhầm với dữ liệu"}},
                    {"id": "D", "text": "Mạng", "is_correct": False, "misconception": {"id": "network", "label": "Nhầm với hạ tầng"}},
                ],
            },
        ],
    }


class LessonSchemaTests(unittest.TestCase):
    def test_valid_lesson_is_normalized(self):
        result = validate_lesson(lesson())
        self.assertEqual(["cp1", "cp2"], [item["id"] for item in result["checkpoints"]])

    def test_rejects_missing_misconception(self):
        data = lesson()
        data["checkpoints"][0]["options"][1]["misconception"] = None
        with self.assertRaisesRegex(ValueError, "misconception"):
            validate_lesson(data)

    def test_rejects_checkpoints_too_close_for_skip(self):
        data = lesson()
        data["checkpoints"][1]["time"] = 29
        with self.assertRaisesRegex(ValueError, "10 seconds"):
            validate_lesson(data)

    def test_first_attempt_score(self):
        self.assertEqual(10.0, checkpoint_score(3, 3))
        self.assertEqual(6.7, checkpoint_score(2, 3))


if __name__ == "__main__":
    unittest.main()
