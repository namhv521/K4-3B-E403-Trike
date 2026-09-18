"""Local-only job, bundle and anonymous telemetry storage for the prototype."""

import json
import os
import shutil
import subprocess
import sys
import threading
import uuid
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath


ALLOWED_UPLOAD_EXTENSIONS = {".md", ".txt", ".pptx", ".pdf", ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp4", ".mov", ".webm", ".mkv"}
ALLOWED_EVENT_FIELDS = {
    "session_id", "timestamp", "event", "video_time", "checkpoint_id", "attempt_number",
    "selected_answer", "is_correct", "misconception_id", "misconception_label",
    "action_after_feedback", "response_time_ms", "score", "input_type", "input_value",
    "seek_from", "seek_to", "first_attempt_accuracy", "answered_checkpoints",
    "total_checkpoints", "total_attempts", "average_response_time_ms", "completion_seconds",
    "duration_seconds", "watched_ratio", "needs_review",
}


def allowed_upload_name(name):
    candidate = PurePosixPath(str(name).replace("\\", "/"))
    return bool(candidate.name and candidate.suffix.lower() in ALLOWED_UPLOAD_EXTENSIONS and not candidate.is_absolute() and ".." not in candidate.parts)


def allowlisted_event(event):
    if not isinstance(event, dict):
        raise ValueError("Event phải là object.")
    result = {key: value for key, value in event.items() if key in ALLOWED_EVENT_FIELDS}
    for field in ("session_id", "timestamp", "event"):
        if not isinstance(result.get(field), str) or not result[field].strip():
            raise ValueError(f"Thiếu {field} hợp lệ.")
    return result


class JobStore:
    def __init__(self, runtime_root):
        self.root = Path(runtime_root).resolve()
        self.jobs = self.root / "jobs"
        self.bundles = self.root / "bundles"
        self.jobs.mkdir(parents=True, exist_ok=True)
        self.bundles.mkdir(parents=True, exist_ok=True)

    def _job_dir(self, job_id):
        if not job_id or "/" in job_id or "\\" in job_id or ".." in job_id:
            raise ValueError("Job id không hợp lệ.")
        return self.jobs / job_id

    def create(self, prompt, files):
        prompt = str(prompt or "").strip()
        if not 8 <= len(prompt) <= 500:
            raise ValueError("Prompt cần từ 8 đến 500 ký tự.")
        if not files:
            raise ValueError("Hãy chọn ít nhất một học liệu.")
        job_id = uuid.uuid4().hex
        root = self._job_dir(job_id)
        source_root = root / "input"
        for name, body in files:
            if not allowed_upload_name(name):
                shutil.rmtree(root, ignore_errors=True)
                raise ValueError("Chỉ nhận học liệu được hỗ trợ; không nhận đường dẫn thoát thư mục hoặc file thực thi.")
            destination = source_root / PurePosixPath(name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(body)
        request = root / "request.json"
        request.write_text(json.dumps({"prompt": prompt}, ensure_ascii=False), encoding="utf-8")
        status = {"id": job_id, "status": "queued", "bundle_id": job_id}
        self._write_status(job_id, status)
        return status

    def _write_status(self, job_id, status):
        path = self._job_dir(job_id) / "status.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(status, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, path)

    def get(self, job_id):
        path = self._job_dir(job_id) / "status.json"
        if not path.is_file():
            raise FileNotFoundError("Không tìm thấy job.")
        return json.loads(path.read_text(encoding="utf-8"))

    def update(self, job_id, **values):
        status = self.get(job_id)
        status.update(values)
        self._write_status(job_id, status)
        return status

    def bundle_dir(self, bundle_id):
        if not bundle_id or "/" in bundle_id or "\\" in bundle_id or ".." in bundle_id:
            raise ValueError("Bundle id không hợp lệ.")
        return self.bundles / bundle_id

    def run(self, job_id, generator_dir):
        source_root = self._job_dir(job_id) / "input"
        request_path = self._job_dir(job_id) / "request.json"
        output = None
        try:
            self.update(job_id, status="running")
            status = self.get(job_id)
            prompt = json.loads(request_path.read_text(encoding="utf-8"))["prompt"]
            output = self.bundle_dir(status["bundle_id"])
            output.mkdir(parents=True, exist_ok=True)
            command = [sys.executable, "agent.py", "--input", str(source_root), "--prompt", prompt, "--output", str(output)]
            environment = {**os.environ, "VLEARN_RENDERER": "remotion"}
            result = subprocess.run(command, cwd=generator_dir, env=environment, capture_output=True, text=True)
            required = [output / name for name in ("lesson.json", "sources.json", "recap.mp4")]
            if result.returncode or not all(item.is_file() and item.stat().st_size > 0 for item in required):
                shutil.rmtree(output, ignore_errors=True)
                return self.update(job_id, status="failed", error="Không thể tạo bundle. Kiểm tra cấu hình OpenRouter, Edge TTS và Remotion trên máy local.")
            return self.update(job_id, status="succeeded", bundle_url=f"/learn/{status['bundle_id']}")
        except (KeyError, OSError, ValueError, json.JSONDecodeError):
            if output:
                shutil.rmtree(output, ignore_errors=True)
            return self.update(job_id, status="failed", error="Không thể tạo bundle. Kiểm tra cấu hình OpenRouter, Edge TTS và Remotion trên máy local.")
        finally:
            shutil.rmtree(source_root, ignore_errors=True)
            request_path.unlink(missing_ok=True)

    def run_async(self, job_id, generator_dir):
        thread = threading.Thread(target=self.run, args=(job_id, generator_dir), daemon=True)
        thread.start()


class TelemetryStore:
    def __init__(self, runtime_root):
        self.root = Path(runtime_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "events.jsonl"
        self.lock = threading.Lock()

    def append(self, bundle_id, event):
        if not bundle_id or "/" in bundle_id or "\\" in bundle_id or ".." in bundle_id:
            raise ValueError("Bundle id không hợp lệ.")
        item = {"bundle_id": bundle_id, **allowlisted_event(event)}
        with self.lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        return item

    def _events(self, bundle_id):
        if not self.path.is_file():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("bundle_id") == bundle_id:
                rows.append(event)
        return rows

    def analytics(self, bundle_id):
        events = self._events(bundle_id)
        sessions = {item["session_id"] for item in events}
        first_answers = {}
        misconceptions = Counter()
        completion = {}
        response_times = []
        for event in events:
            if event["event"] == "answer_submitted" and event.get("checkpoint_id"):
                key = (event["session_id"], event["checkpoint_id"])
                if key not in first_answers:
                    first_answers[key] = event
                if event.get("is_correct") is False and event.get("misconception_id"):
                    misconceptions[(event["misconception_id"], event.get("misconception_label", ""))] += 1
                if isinstance(event.get("response_time_ms"), (int, float)):
                    response_times.append(event["response_time_ms"])
            if event["event"] == "session_completed":
                completion[event["session_id"]] = event
        checkpoints = defaultdict(list)
        for (_, checkpoint_id), event in first_answers.items():
            checkpoints[checkpoint_id].append(event)
        rows = []
        for checkpoint_id, answers in checkpoints.items():
            correct = sum(item.get("is_correct") is True for item in answers)
            rows.append({"checkpoint_id": checkpoint_id, "attempts": len(answers), "first_attempt_accuracy": round(correct * 100 / len(answers)), "incorrect": len(answers) - correct})
        rows.sort(key=lambda row: (-row["incorrect"], row["checkpoint_id"]))
        session_rows = []
        for session_id in sessions:
            session_events = [event for event in events if event["session_id"] == session_id]
            last_event = max(session_events, key=lambda event: event["timestamp"])
            session_rows.append({
                "session_id": session_id,
                "event_count": len(session_events),
                "last_event_at": last_event["timestamp"],
                "completed": session_id in completion,
            })
        session_rows.sort(key=lambda row: (row["last_event_at"], row["session_id"]), reverse=True)
        recent_events = [
            {
                "session_id": event["session_id"],
                "timestamp": event["timestamp"],
                "event": event["event"],
                "checkpoint_id": event.get("checkpoint_id"),
                "is_correct": event.get("is_correct"),
            }
            for event in sorted(events, key=lambda event: (event["timestamp"], event["session_id"]))[-20:]
        ]
        return {
            "views": len(sessions), "completed_sessions": len(completion),
            "fast_completion_count": sum(item.get("needs_review") is True for item in completion.values()),
            "average_response_time_ms": round(sum(response_times) / len(response_times)) if response_times else 0,
            "average_completion_seconds": round(sum(item.get("completion_seconds", 0) for item in completion.values()) / len(completion)) if completion else 0,
            "checkpoints": rows,
            "misconceptions": [{"misconception_id": key[0], "label": key[1], "count": count} for key, count in misconceptions.most_common()],
            "sessions": session_rows[:20],
            "recent_events": recent_events,
        }
