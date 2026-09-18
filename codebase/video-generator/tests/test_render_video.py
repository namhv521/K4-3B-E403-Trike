import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from render_video import render_video


class RenderVideoTests(unittest.TestCase):
    def test_video_render_is_limited_by_manifest_duration_not_audio_shortest(self):
        captured = []

        def runner(command, **kwargs):
            captured.extend(command)
            return type("Result", (), {"returncode": 0, "stderr": ""})()

        lesson = {
            "duration_seconds": 85,
            "scenes": [{"start": 0, "end": 85, "title": "Khung", "body": "Nội dung"}],
        }
        with patch("render_video.shutil.which", return_value="ffmpeg"), patch("render_video.subprocess.run", side_effect=runner):
            render_video(lesson, None, Path("C:/tmp/recap.mp4"))
        self.assertIn("-t", captured)
        self.assertEqual(85.0, float(captured[captured.index("-t") + 1]))
        self.assertNotIn("-shortest", captured)


if __name__ == "__main__":
    unittest.main()