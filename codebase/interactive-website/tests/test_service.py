import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from service import JobStore, TelemetryStore, allowed_upload_name


class ServiceTests(unittest.TestCase):
    def test_upload_allowlist_rejects_untrusted_executable_and_paths(self):
        self.assertTrue(allowed_upload_name("slides/week-1.pptx"))
        self.assertFalse(allowed_upload_name("../secret.pdf"))
        self.assertFalse(allowed_upload_name("lesson.exe"))

    def test_telemetry_strips_secrets_and_aggregates_misconceptions(self):
        with TemporaryDirectory() as folder:
            telemetry = TelemetryStore(Path(folder))
            telemetry.append("bundle-1", {
                "session_id": "session-1", "timestamp": "2026-09-18T00:00:00Z",
                "event": "answer_submitted", "checkpoint_id": "cp-1", "is_correct": False,
                "misconception_id": "scope", "misconception_label": "Nhầm phạm vi",
                "api_key": "secret",
            })
            telemetry.append("bundle-1", {
                "session_id": "session-2", "timestamp": "2026-09-18T00:01:00Z",
                "event": "answer_submitted", "checkpoint_id": "cp-1", "is_correct": True,
            })
            report = telemetry.analytics("bundle-1")
            event = json.loads((Path(folder) / "events.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertNotIn("api_key", event)
        self.assertEqual(report["views"], 2)
        self.assertEqual(report["checkpoints"][0]["checkpoint_id"], "cp-1")
        self.assertEqual(report["checkpoints"][0]["first_attempt_accuracy"], 50)
        self.assertEqual(report["misconceptions"][0]["misconception_id"], "scope")

    def test_job_store_rejects_paths_outside_runtime(self):
        with TemporaryDirectory() as folder:
            jobs = JobStore(Path(folder))
            job = jobs.create("Tạo video ôn tập", [("slides/lesson.md", "Nội dung".encode("utf-8"))])
            self.assertTrue((Path(folder) / "jobs" / job["id"] / "input" / "slides" / "lesson.md").is_file())
            with self.assertRaises(ValueError):
                jobs.create("Tạo video", [("../../outside.md", "Nội dung".encode("utf-8"))])
