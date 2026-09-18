import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_tts import generate_tts


class TtsTests(unittest.TestCase):
    def test_audio_is_padded_to_lesson_duration(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            Path(command[command.index("--write-media") + 1]).write_bytes(b"voice")
            return subprocess.CompletedProcess(command, 0, "", "")

        def aligner(command, **kwargs):
            Path(command[-1]).write_bytes(b"aligned-voice")
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder, "voice.mp3")
            trace = generate_tts(
                {"narration": "Xin chào", "duration_seconds": 80}, None, output,
                runner=runner, aligner=aligner,
            )
            self.assertEqual(b"aligned-voice", output.read_bytes())
        self.assertIn("apad", " ".join(calls[0]) + " " + trace["alignment"])
        self.assertEqual(80, trace["duration_seconds"])
    def test_public_tts_writes_non_empty_audio(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            Path(command[command.index("--write-media") + 1]).write_bytes(b"voice")
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder, "voice.mp3")
            trace = generate_tts({"narration": "Xin chào"}, None, output, runner=runner)
            self.assertEqual(b"voice", output.read_bytes())
        self.assertIn("edge_tts", calls[0])
        self.assertEqual("edge-tts", trace["provider"])

    def test_public_tts_rejects_empty_audio(self):
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "empty audio"):
                generate_tts({"narration": "Xin chào"}, None, Path(folder, "voice.mp3"), runner=runner)

    def test_public_tts_retries_a_transient_failure(self):
        attempts = 0

        def runner(command, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return subprocess.CompletedProcess(command, 1, "", "NoAudioReceived")
            Path(command[command.index("--write-media") + 1]).write_bytes(b"voice")
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as folder:
            generate_tts({"narration": "Xin chào"}, None, Path(folder, "voice.mp3"), runner=runner)
        self.assertEqual(2, attempts)


if __name__ == "__main__":
    unittest.main()
