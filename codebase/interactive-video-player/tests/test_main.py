import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import load_bundle, writable_root
from lesson_schema import validate_lesson


class BundleTests(unittest.TestCase):
    def test_requires_all_three_generated_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "lesson.json"):
                load_bundle(Path(folder))

    def test_rejects_malformed_lesson(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            malformed = {"title": "Recap", "narration": "Nội dung", "duration_seconds": 60, "scenes": [{}]}
            (root / "lesson.json").write_text(json.dumps(malformed), encoding="utf-8")
            (root / "recap.mp4").write_bytes(b"video")
            (root / "narration.mp3").write_bytes(b"audio")
            with self.assertRaisesRegex(ValueError, "checkpoints"):
                load_bundle(root)

    def test_rejects_non_object_lesson(self):
        with self.assertRaisesRegex(ValueError, "object"):
            validate_lesson([])

    def test_rejects_incomplete_checkpoint_before_gui_startup(self):
        invalid = {
            "title": "Recap", "narration": "Nội dung", "duration_seconds": 60,
            "scenes": [{"start": 0, "end": 60, "title": "Khung", "body": "Nội dung", "source_refs": ["fixture:1"]}], "checkpoints": [{"id": "cp1"}],
        }
        with self.assertRaisesRegex(ValueError, "time"):
            validate_lesson(invalid)

    def test_loads_valid_bundle(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            options = [{"id": "A", "text": "Đúng", "is_correct": True, "misconception": None}]
            options += [
                {"id": key, "text": f"Sai {key}", "is_correct": False,
                 "misconception": {"id": key.lower(), "label": f"Nhầm {key}"}}
                for key in ("B", "C", "D")
            ]
            lesson = {
                "title": "Recap", "narration": "Nội dung", "duration_seconds": 60,
                "scenes": [{"start": 0, "end": 60, "title": "Khung", "body": "Nội dung", "source_refs": ["fixture:1"]}],
                "checkpoints": [{
                    "id": "cp1", "time": 20, "concept": "AI", "question": "AI là gì?",
                    "explanation": "AI là lĩnh vực rộng.", "source_refs": ["fixture:1"], "options": options,
                }],
            }
            (root / "lesson.json").write_text(json.dumps(lesson), encoding="utf-8")
            (root / "recap.mp4").write_bytes(b"video")
            (root / "narration.mp3").write_bytes(b"audio")
            loaded, video, audio = load_bundle(root)
            self.assertEqual("Recap", loaded["title"])
            self.assertEqual("recap.mp4", video.name)
            self.assertEqual("narration.mp3", audio.name)

    def test_packaged_logs_are_written_to_user_data(self):
        with patch.object(sys, "frozen", True, create=True), patch.dict("os.environ", {"LOCALAPPDATA": r"C:\Users\Nam\AppData\Local"}):
            self.assertEqual(Path(r"C:\Users\Nam\AppData\Local\InteractiveRecap"), writable_root())


if __name__ == "__main__":
    unittest.main()
