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

    def test_analytics_reports_anonymous_session_metrics_and_safe_recent_events(self):
        with TemporaryDirectory() as folder:
            telemetry = TelemetryStore(Path(folder))
            telemetry.append("bundle-1", {
                "session_id": "session-1", "timestamp": "2026-09-18T00:00:00Z",
                "event": "answer_submitted", "checkpoint_id": "cp-1", "is_correct": False,
                "response_time_ms": 1000, "input_value": "B",
            })
            telemetry.append("bundle-1", {
                "session_id": "session-1", "timestamp": "2026-09-18T00:00:10Z",
                "event": "answer_submitted", "checkpoint_id": "cp-1", "is_correct": True,
                "response_time_ms": 3000,
            })
            telemetry.append("bundle-1", {
                "session_id": "session-1", "timestamp": "2026-09-18T00:01:00Z",
                "event": "session_completed", "completion_seconds": 40, "needs_review": False,
            })
            telemetry.append("bundle-1", {
                "session_id": "session-2", "timestamp": "2026-09-18T00:02:00Z",
                "event": "answer_submitted", "checkpoint_id": "cp-1", "is_correct": True,
                "response_time_ms": 5000,
            })
            telemetry.append("bundle-1", {
                "session_id": "session-2", "timestamp": "2026-09-18T00:03:00Z",
                "event": "session_completed", "completion_seconds": 60, "needs_review": True,
            })
            report = telemetry.analytics("bundle-1")

        self.assertEqual(report["average_response_time_ms"], 3000)
        self.assertEqual(report["average_completion_seconds"], 50)
        self.assertEqual(report["fast_completion_count"], 1)
        self.assertEqual(report["sessions"], [
            {"session_id": "session-2", "event_count": 2, "last_event_at": "2026-09-18T00:03:00Z", "completed": True},
            {"session_id": "session-1", "event_count": 3, "last_event_at": "2026-09-18T00:01:00Z", "completed": True},
        ])
        self.assertEqual(
            [event["timestamp"] for event in report["recent_events"]],
            [
                "2026-09-18T00:00:00Z",
                "2026-09-18T00:00:10Z",
                "2026-09-18T00:01:00Z",
                "2026-09-18T00:02:00Z",
                "2026-09-18T00:03:00Z",
            ],
        )
        self.assertEqual(report["recent_events"][-1], {
            "session_id": "session-2", "timestamp": "2026-09-18T00:03:00Z",
            "event": "session_completed", "checkpoint_id": None, "is_correct": None,
        })
        self.assertNotIn("input_value", report["recent_events"][0])

    def test_job_store_rejects_paths_outside_runtime(self):
        with TemporaryDirectory() as folder:
            jobs = JobStore(Path(folder))
            job = jobs.create("Tạo video ôn tập", [("slides/lesson.md", "Nội dung".encode("utf-8"))])
            self.assertTrue((Path(folder) / "jobs" / job["id"] / "input" / "slides" / "lesson.md").is_file())
            with self.assertRaises(ValueError):
                jobs.create("Tạo video", [("../../outside.md", "Nội dung".encode("utf-8"))])

    def test_job_status_never_exposes_generation_prompt(self):
        with TemporaryDirectory() as folder:
            jobs = JobStore(Path(folder))
            job = jobs.create("Tạo video recap kín đáo", [("lesson.md", b"Noi dung")])

            self.assertNotIn("prompt", job)
            self.assertNotIn("prompt", jobs.get(job["id"]))
            self.assertEqual(
                json.loads((Path(folder) / "jobs" / job["id"] / "request.json").read_text(encoding="utf-8")),
                {"prompt": "Tạo video recap kín đáo"},
            )
