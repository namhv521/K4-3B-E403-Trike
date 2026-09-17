import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import append_event, parse_byte_range, sanitize_event


class ServerTests(unittest.TestCase):
    def test_parses_single_http_byte_range(self):
        self.assertEqual(parse_byte_range("bytes=100-199", 1000), (100, 199))
        self.assertEqual(parse_byte_range("bytes=900-", 1000), (900, 999))
        self.assertEqual(parse_byte_range("bytes=-100", 1000), (900, 999))
        with self.assertRaises(ValueError):
            parse_byte_range("bytes=1000-1001", 1000)

    def test_valid_event_is_appended_as_jsonl(self):
        event = {"session_id": "s1", "timestamp": "2026-09-18T00:00:00Z", "event": "answer_submitted", "checkpoint_id": "cp1", "selected_answer": "B"}
        with tempfile.TemporaryDirectory() as folder:
            path = append_event(Path(folder), event, now=datetime(2026, 9, 18, tzinfo=timezone.utc))
            saved = json.loads(path.read_text(encoding="utf-8").strip())
        self.assertEqual("s1", saved["session_id"])
        self.assertEqual("B", saved["selected_answer"])

    def test_rejects_invalid_event(self):
        with self.assertRaisesRegex(ValueError, "session_id"):
            sanitize_event({"event": "answer_submitted"})

    def test_secret_fields_are_not_persisted(self):
        clean = sanitize_event({"session_id": "s1", "timestamp": "x", "event": "x", "api_key": "secret", "token": "secret"})
        self.assertNotIn("api_key", clean)
        self.assertNotIn("token", clean)

    def test_unknown_fields_are_dropped(self):
        clean = sanitize_event({"session_id": "s1", "timestamp": "x", "event": "x", "../../path": "bad"})
        self.assertNotIn("../../path", clean)


if __name__ == "__main__":
    unittest.main()
