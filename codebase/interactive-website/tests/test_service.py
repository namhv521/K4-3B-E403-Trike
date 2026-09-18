import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from service import JobStore, LectureStore, TelemetryStore, UserStore, allowed_upload_name, generation_error_message, sanitize_generation_log


class ServiceTests(unittest.TestCase):
    def test_lecture_store_bootstraps_four_lectures_and_puts_existing_video_in_lecture_one(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            assets = root / "assets"
            assets.mkdir()
            (assets / "lesson.json").write_text(json.dumps({"title": "Bản đồ AI trong 85s", "checkpoints": [{"id": "cp-1"}]}), encoding="utf-8")
            (assets / "sources.json").write_text("[]", encoding="utf-8")
            (assets / "recap.mp4").write_bytes(b"video")
            lectures = LectureStore(root / "runtime", JobStore(root / "runtime"))

            lectures.ensure_lecture_one(assets)
            catalog = lectures.list()

            self.assertEqual([item["lecture_id"] for item in catalog], ["lecture1", "lecture2", "lecture3", "lecture4"])
            self.assertEqual(catalog[0], {
                "lecture_id": "lecture1", "title": "Lecture 1", "published": True,
                "lesson_title": "Bản đồ AI trong 85s", "checkpoint_count": 1, "bundle_url": "/learn/lecture1",
            })
            self.assertFalse(catalog[1]["published"])
            self.assertTrue((root / "runtime" / "bundles" / "lecture1" / "recap.mp4").is_file())

    def test_local_users_are_created_safely_and_analytics_identifies_the_test_user(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            users = UserStore(root / "runtime")
            learner = users.create("Minh Anh")
            telemetry = TelemetryStore(root / "runtime" / "telemetry")
            telemetry.append("lecture1", {
                "session_id": "session-1", "timestamp": "2026-09-18T00:00:00Z", "event": "video_play",
                "user_id": learner["id"], "user_name": learner["name"],
            })
            report = telemetry.analytics("lecture1")

            self.assertEqual(learner["name"], "Minh Anh")
            self.assertEqual(report["users"], [{"user_id": learner["id"], "user_name": "Minh Anh", "event_count": 1, "last_event_at": "2026-09-18T00:00:00Z", "completed": False}])
            self.assertEqual(report["recent_events"][0]["user_name"], "Minh Anh")
            with self.assertRaisesRegex(ValueError, "Tên user"):
                users.create("<script>")

    def test_generation_error_message_explains_missing_openrouter_key(self):
        message = generation_error_message("RuntimeError: OPENROUTER_API_KEY is not configured", 1)

        self.assertIn("OPENROUTER_API_KEY", message)
        self.assertIn("PowerShell", message)

    def test_generation_error_message_explains_timeout(self):
        message = generation_error_message("Generation timed out after 300 seconds")

        self.assertIn("quá thời gian", message)
        self.assertIn("OpenRouter/free", message)

    def test_generation_error_message_explains_invalid_model_lesson(self):
        message = generation_error_message("ValueError: Model returned an invalid interactive lesson after 3 attempts: scene 0 title must be non-empty text", 1)

        self.assertIn("OpenRouter", message)
        self.assertIn("thiếu trường", message)

    def test_generation_diagnostics_redact_openrouter_keys(self):
        diagnostic = sanitize_generation_log("OpenRouter failed with Bearer sk-or-v1-secret-value")

        self.assertNotIn("sk-or-v1-secret-value", diagnostic)
        self.assertIn("[REDACTED]", diagnostic)

    def test_upload_allowlist_rejects_untrusted_executable_and_paths(self):
        self.assertTrue(allowed_upload_name("slides/week-1.pptx"))
        self.assertTrue(allowed_upload_name("documents/lesson.docx"))
        self.assertFalse(allowed_upload_name("../secret.pdf"))
        self.assertFalse(allowed_upload_name("lesson.exe"))

    def test_job_store_explains_that_legacy_powerpoint_must_be_converted_to_pptx(self):
        with TemporaryDirectory() as folder:
            jobs = JobStore(Path(folder))

            with self.assertRaisesRegex(ValueError, r"PowerPoint \.ppt cũ.*\.pptx"):
                jobs.create("Tạo video recap từ slide", [("slides/lecture-1.ppt", b"legacy")])

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

    def test_analytics_reports_average_score_and_completed_anonymous_session_scores(self):
        with TemporaryDirectory() as folder:
            telemetry = TelemetryStore(Path(folder))
            telemetry.append("bundle-1", {
                "session_id": "session-low", "timestamp": "2026-09-18T00:01:00Z",
                "event": "session_completed", "score": 4,
                "first_attempt_accuracy": 40,
            })
            telemetry.append("bundle-1", {
                "session_id": "session-high", "timestamp": "2026-09-18T00:02:00Z",
                "event": "session_completed", "score": 8,
                "first_attempt_accuracy": 80,
            })
            telemetry.append("bundle-other", {
                "session_id": "session-other", "timestamp": "2026-09-18T00:03:00Z",
                "event": "session_completed", "score": 10,
            })
            report = telemetry.analytics("bundle-1")

        self.assertEqual(report["average_score"], 6)
        self.assertEqual(report["sessions"], [
            {"session_id": "session-high", "event_count": 1, "last_event_at": "2026-09-18T00:02:00Z", "completed": True, "score": 8, "first_attempt_accuracy": 80},
            {"session_id": "session-low", "event_count": 1, "last_event_at": "2026-09-18T00:01:00Z", "completed": True, "score": 4, "first_attempt_accuracy": 40},
        ])

    def test_job_store_lists_only_published_lectures_with_safe_metadata(self):
        with TemporaryDirectory() as folder:
            jobs = JobStore(Path(folder))
            published = jobs.bundle_dir("lecture-1")
            published.mkdir(parents=True)
            (published / "lesson.json").write_text(json.dumps({
                "title": "Lecture về AI", "checkpoints": [{"id": "cp-1"}, {"id": "cp-2"}],
            }), encoding="utf-8")
            (published / "sources.json").write_text("[]", encoding="utf-8")
            (published / "recap.mp4").write_bytes(b"video")
            incomplete = jobs.bundle_dir("unfinished")
            incomplete.mkdir(parents=True)
            (incomplete / "lesson.json").write_text("{}", encoding="utf-8")

            lectures = jobs.list_published_bundles()

        self.assertEqual(lectures, [{
            "bundle_id": "lecture-1", "title": "Lecture về AI", "checkpoint_count": 2,
        }])

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
