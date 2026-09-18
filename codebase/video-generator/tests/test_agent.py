import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import generate, publish_fixture, require_lesson_sources


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

            def tts_generator(lesson, client, output):
                output.write_bytes(b"voice")
                return {"provider": "test"}

            publish_fixture(fixture, root / "out", renderer=renderer, tts_generator=tts_generator)
            manifest = json.loads((root / "out" / "lesson.json").read_text(encoding="utf-8"))
            trace = json.loads((root / "out" / "ai-trace.json").read_text(encoding="utf-8"))
            self.assertEqual("mock", manifest["generation"]["mode"])
            self.assertFalse(trace["ai_called"])
            self.assertEqual(b"video", (root / "out" / "recap.mp4").read_bytes())

    def test_fixture_passes_generated_voice_to_renderer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fixture = root / "lesson.json"
            fixture.write_text(json.dumps(LESSON, ensure_ascii=False), encoding="utf-8")
            received = []

            def tts_generator(lesson, client, output):
                output.write_bytes(b"voice")
                return {"provider": "test"}

            def renderer(lesson, narration, output):
                received.append((narration.name, narration.read_bytes()))
                output.write_bytes(b"video")

            publish_fixture(fixture, root / "out", renderer=renderer, tts_generator=tts_generator)
            self.assertEqual(("narration.mp3", b"voice"), received[0])

    def test_template_only_input_is_rejected(self):
        records = [{"source": "input/mau-kich-ban.md", "locator": "line:1", "text": "Mẫu kịch bản chung"}]
        with self.assertRaisesRegex(ValueError, "nội dung bài giảng"):
            require_lesson_sources(records)

    def test_generate_reports_template_error_before_api_key_error(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "input"
            source.mkdir()
            (source / "mau-kich-ban.md").write_text("# Mẫu kịch bản", encoding="utf-8")
            with patch.dict("os.environ", {"OPENROUTER_API_KEY": ""}):
                with self.assertRaisesRegex(ValueError, "nội dung bài giảng"):
                    generate(source, "Tạo video", root / "out")


if __name__ == "__main__":
    unittest.main()
