import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from render_video import remotion_command


class RemotionRendererTests(unittest.TestCase):
    def test_command_renders_generic_vlearn_composition_with_lesson_props(self):
        lesson = {
            "title": "Ôn AI",
            "duration_seconds": 60,
            "scenes": [{"start": 0, "end": 60, "title": "AI", "body": "Khái niệm"}],
        }
        with TemporaryDirectory() as folder:
            command = remotion_command(lesson, Path(folder) / "narration.mp3", Path(folder) / "recap.mp4")
        self.assertEqual(command[0], "node")
        self.assertEqual(command[2:5], ["render", "src/index.ts", "VLearnRecap"])
        self.assertIn("--props", command)
        props = json.loads(command[command.index("--props") + 1])
        self.assertEqual(props["lesson"]["title"], "Ôn AI")
        self.assertEqual(props["narrationPath"], "narration.mp3")
        self.assertEqual(Path(command[5]).name, "recap.mp4")
