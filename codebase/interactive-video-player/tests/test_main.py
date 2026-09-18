import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import load_bundle, writable_root


class BundleTests(unittest.TestCase):
    def test_requires_all_three_generated_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "lesson.json"):
                load_bundle(Path(folder))

    def test_rejects_malformed_lesson(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "lesson.json").write_text("{}", encoding="utf-8")
            (root / "recap.mp4").write_bytes(b"video")
            (root / "narration.mp3").write_bytes(b"audio")
            with self.assertRaisesRegex(ValueError, "checkpoints"):
                load_bundle(root)

    def test_loads_valid_bundle(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            lesson = {"title": "Recap", "duration_seconds": 60, "checkpoints": [{"id": "cp1"}]}
            (root / "lesson.json").write_text(json.dumps(lesson), encoding="utf-8")
            (root / "recap.mp4").write_bytes(b"video")
            (root / "narration.mp3").write_bytes(b"audio")
            loaded, video, audio = load_bundle(root)
            self.assertEqual("Recap", loaded["title"])
            self.assertEqual("recap.mp4", video.name)
            self.assertEqual("narration.mp3", audio.name)

    def test_packaged_logs_are_written_next_to_executable(self):
        with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", r"C:\Recap\recap-player.exe"):
            self.assertEqual(Path(r"C:\Recap"), writable_root())


if __name__ == "__main__":
    unittest.main()
