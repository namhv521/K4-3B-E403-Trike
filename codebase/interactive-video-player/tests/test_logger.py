import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from logger import append_event


class LoggerTests(unittest.TestCase):
    def test_appends_allowlisted_json_without_secrets(self):
        event = {
            "session_id": "s1", "timestamp": "2026-09-18T00:00:00Z",
            "event": "answer_submitted", "selected_answer": "B",
            "misconception_id": "scope", "api_key": "secret", "source_text": "private",
        }
        with tempfile.TemporaryDirectory() as folder:
            path = append_event(Path(folder), event, now=datetime(2026, 9, 18, tzinfo=timezone.utc))
            saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual("B", saved["selected_answer"])
        self.assertNotIn("api_key", saved)
        self.assertNotIn("source_text", saved)

    def test_rejects_event_without_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "session_id"):
                append_event(Path(folder), {"event": "x", "timestamp": "now"})


if __name__ == "__main__":
    unittest.main()
