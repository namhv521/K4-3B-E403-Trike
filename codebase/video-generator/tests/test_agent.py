import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import publish_fixture


LESSON = {
    "version": 1,
    "title": "AI trong một phút",
    "duration_seconds": 36,
    "narration": "AI là lĩnh vực rộng. Học máy là một cách làm trong AI.",
    "scenes": [{"start": 0, "end": 36, "title": "Bản đồ AI", "body": "AI rộng hơn học máy", "source_refs": ["fixture:1"]}],
    "checkpoints": [
        {
            "id": "cp1", "time": 15, "concept": "AI", "question": "Khái niệm nào rộng hơn?", "explanation": "AI là lĩnh vực rộng.", "source_refs": ["fixture:1"],
            "options": [
                {"id": "A", "text": "AI", "is_correct": True, "misconception": None},
                {"id": "B", "text": "Học máy", "is_correct": False, "misconception": {"id": "scope", "label": "Đảo quan hệ phạm vi"}},
                {"id": "C", "text": "Email", "is_correct": False, "misconception": {"id": "example", "label": "Nhầm ví dụ với lĩnh vực"}},
                {"id": "D", "text": "Dữ liệu", "is_correct": False, "misconception": {"id": "data", "label": "Nhầm dữ liệu với lĩnh vực"}}
            ]
        }
    ]
}


class AgentTests(unittest.TestCase):
    def test_fixture_output_is_explicitly_marked_mock(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fixture = root / "lesson.json"
            fixture.write_text(json.dumps(LESSON, ensure_ascii=False), encoding="utf-8")

            def renderer(lesson, narration, output):
                output.write_bytes(b"video")
                return output

            publish_fixture(fixture, root / "out", renderer=renderer)
            manifest = json.loads((root / "out" / "lesson.json").read_text(encoding="utf-8"))
            trace = json.loads((root / "out" / "ai-trace.json").read_text(encoding="utf-8"))
            self.assertEqual("mock", manifest["generation"]["mode"])
            self.assertFalse(trace["ai_called"])
            self.assertEqual(b"video", (root / "out" / "recap.mp4").read_bytes())


if __name__ == "__main__":
    unittest.main()
