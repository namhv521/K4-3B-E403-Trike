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


ALLOWED_UPLOAD_EXTENSIONS = {".md", ".txt", ".pptx", ".docx", ".pdf", ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp4", ".mov", ".webm", ".mkv"}
ALLOWED_EVENT_FIELDS = {
    "session_id", "timestamp", "event", "user_id", "user_name", "video_time", "checkpoint_id", "attempt_number",
    "selected_answer", "is_correct", "misconception_id", "misconception_label",
    "action_after_feedback", "response_time_ms", "score", "input_type", "input_value",
    "seek_from", "seek_to", "first_attempt_accuracy", "answered_checkpoints",
    "total_checkpoints", "total_attempts", "average_response_time_ms", "completion_seconds",
    "duration_seconds", "watched_ratio", "needs_review",
}
GENERATION_TIMEOUT_SECONDS = 300
LECTURE_IDS = ("lecture1", "lecture2", "lecture3", "lecture4")


def generation_error_message(stderr, return_code=None):
    """Map generator failures to a safe, actionable message for the local admin."""
    detail = str(stderr or "")
    normalized = detail.casefold()
    if "openrouter_api_key is not configured" in normalized:
        return "OpenRouter chưa nhận OPENROUTER_API_KEY. Đóng server, mở PowerShell mới rồi chạy lại server."
    if "openrouter returned http 401" in normalized or "openrouter returned http 403" in normalized:
        return "OpenRouter từ chối API key. Kiểm tra OPENROUTER_API_KEY rồi khởi động lại server."
    if "remotion renderer is not installed" in normalized:
        return "Remotion chưa được cài. Chạy npm install trong video-generator/remotion-recap rồi khởi động lại server."
    if "remotion render failed" in normalized:
        return "Remotion không render được video. Kiểm tra Chrome/Edge, Node.js và thử lại."
    if "edge tts failed" in normalized or "edge tts returned empty audio" in normalized:
        return "Edge TTS không tạo được audio. Kiểm tra kết nối Internet rồi thử lại."
    if "file is not a zip file" in normalized or "badzipfile" in normalized:
        return "File Office đã chọn không hợp lệ hoặc bị hỏng. Hãy mở file và lưu lại thành .pptx/.docx rồi thử lại."
    if "every source record must map to a published source reference" in normalized:
        return "Không thể lập citation cho học liệu đã tải lên. Hãy thử lại sau khi khởi động lại server."
    if "model returned an invalid interactive lesson" in normalized or "scene 0 title must be non-empty text" in normalized:
        return "OpenRouter trả lesson thiếu trường bắt buộc. Hệ thống đã yêu cầu tạo lại; hãy thử lại hoặc chọn model ổn định hơn."
    if "generation timed out" in normalized:
        return "Tạo bundle quá thời gian chờ. OpenRouter/free có thể đang chậm; hãy thử lại hoặc chọn model ổn định hơn."
    suffix = f" (mã tiến trình {return_code})" if return_code else ""
    return f"Không thể tạo bundle{suffix}. Kiểm tra generation.log trong runtime/jobs của job này."


def sanitize_generation_log(stderr):
    """Keep local diagnostics useful without retaining secrets or large content."""
    detail = str(stderr or "")[-4_000:]
    for marker in ("sk-or-v1-", "Bearer "):
        start = detail.find(marker)
        while start >= 0:
            end = detail.find(" ", start)
            end = len(detail) if end < 0 else end
            detail = f"{detail[:start]}[REDACTED]{detail[end:]}"
            start = detail.find(marker, start + len("[REDACTED]"))
    return detail


def allowed_upload_name(name):
    candidate = PurePosixPath(str(name).replace("\\", "/"))
    return bool(candidate.name and candidate.suffix.lower() in ALLOWED_UPLOAD_EXTENSIONS and not candidate.is_absolute() and ".." not in candidate.parts)


def upload_validation_error(name):
    candidate = PurePosixPath(str(name).replace("\\", "/"))
    if candidate.suffix.lower() == ".ppt" and candidate.name and not candidate.is_absolute() and ".." not in candidate.parts:
        return "File PowerPoint .ppt cũ chưa được hỗ trợ. Hãy mở và lưu lại thành .pptx trước khi tạo video."
    return "Chỉ nhận học liệu được hỗ trợ; không nhận đường dẫn thoát thư mục hoặc file thực thi."


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

    def create(self, prompt, files, lecture_id=None):
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
                raise ValueError(upload_validation_error(name))
            destination = source_root / PurePosixPath(name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(body)
        request = root / "request.json"
        request.write_text(json.dumps({"prompt": prompt}, ensure_ascii=False), encoding="utf-8")
        bundle_id = lecture_id or job_id
        if not bundle_id or "/" in bundle_id or "\\" in bundle_id or ".." in bundle_id:
            raise ValueError("Lecture không hợp lệ.")
        status = {"id": job_id, "status": "queued", "bundle_id": bundle_id, "lecture_id": bundle_id}
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

    def list_published_bundles(self):
        bundles = []
        for root in self.bundles.iterdir():
            if not root.is_dir() or not all((root / name).is_file() for name in ("lesson.json", "sources.json", "recap.mp4")):
                continue
            try:
                lesson = json.loads((root / "lesson.json").read_text(encoding="utf-8"))
                title = str(lesson["title"]).strip()
                checkpoints = lesson["checkpoints"]
                if not title or not isinstance(checkpoints, list):
                    continue
            except (KeyError, TypeError, ValueError, json.JSONDecodeError, OSError):
                continue
            bundles.append({"bundle_id": root.name, "title": title, "checkpoint_count": len(checkpoints)})
        return sorted(bundles, key=lambda bundle: (bundle["title"].casefold(), bundle["bundle_id"]))

    def _publish(self, source, bundle_id):
        target = self.bundle_dir(bundle_id)
        temporary = target.with_name(f".{target.name}-{uuid.uuid4().hex}.tmp")
        backup = target.with_name(f".{target.name}-{uuid.uuid4().hex}.backup")
        shutil.copytree(source, temporary)
        try:
            if target.exists():
                os.replace(target, backup)
            os.replace(temporary, target)
        except OSError:
            if backup.exists() and not target.exists():
                os.replace(backup, target)
            raise
        finally:
            shutil.rmtree(temporary, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)

    def run(self, job_id, generator_dir):
        source_root = self._job_dir(job_id) / "input"
        request_path = self._job_dir(job_id) / "request.json"
        output = None
        try:
            self.update(job_id, status="running")
            status = self.get(job_id)
            prompt = json.loads(request_path.read_text(encoding="utf-8"))["prompt"]
            output = self._job_dir(job_id) / "output"
            output.mkdir(parents=True, exist_ok=True)
            command = [sys.executable, "agent.py", "--input", str(source_root), "--prompt", prompt, "--output", str(output)]
            environment = {**os.environ, "VLEARN_RENDERER": "remotion"}
            result = subprocess.run(command, cwd=generator_dir, env=environment, capture_output=True, text=True, timeout=GENERATION_TIMEOUT_SECONDS)
            required = [output / name for name in ("lesson.json", "sources.json", "recap.mp4")]
            if result.returncode or not all(item.is_file() and item.stat().st_size > 0 for item in required):
                shutil.rmtree(output, ignore_errors=True)
                diagnostic = self._job_dir(job_id) / "generation.log"
                diagnostic.write_text(sanitize_generation_log(result.stderr), encoding="utf-8")
                return self.update(job_id, status="failed", error=generation_error_message(result.stderr, result.returncode))
            self._publish(output, status["bundle_id"])
            shutil.rmtree(output, ignore_errors=True)
            return self.update(job_id, status="succeeded", bundle_url=f"/learn/{status['bundle_id']}")
        except subprocess.TimeoutExpired:
            if output:
                shutil.rmtree(output, ignore_errors=True)
            detail = f"Generation timed out after {GENERATION_TIMEOUT_SECONDS} seconds"
            (self._job_dir(job_id) / "generation.log").write_text(detail, encoding="utf-8")
            return self.update(job_id, status="failed", error=generation_error_message(detail))
        except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
            if output:
                shutil.rmtree(output, ignore_errors=True)
            detail = f"{type(error).__name__}: {error}"
            (self._job_dir(job_id) / "generation.log").write_text(sanitize_generation_log(detail), encoding="utf-8")
            return self.update(job_id, status="failed", error=generation_error_message(detail))
        finally:
            shutil.rmtree(source_root, ignore_errors=True)
            request_path.unlink(missing_ok=True)

    def run_async(self, job_id, generator_dir):
        thread = threading.Thread(target=self.run, args=(job_id, generator_dir), daemon=True)
        thread.start()


class LectureStore:
    """Fixed local lecture catalogue backed by published JobStore bundles."""

    def __init__(self, runtime_root, jobs):
        self.root = Path(runtime_root).resolve()
        self.path = self.root / "catalog.json"
        self.jobs = jobs
        self.lock = threading.Lock()
        self.root.mkdir(parents=True, exist_ok=True)

    def _records(self):
        if self.path.is_file():
            try:
                saved = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(saved, list) and [item.get("lecture_id") for item in saved] == list(LECTURE_IDS):
                    return saved
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        return [{"lecture_id": lecture_id, "title": f"Lecture {index + 1}", "bundle_id": lecture_id} for index, lecture_id in enumerate(LECTURE_IDS)]

    def _write(self, records):
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, self.path)

    def ensure_lecture_one(self, asset_root):
        source = Path(asset_root).resolve()
        required = ("lesson.json", "sources.json", "recap.mp4")
        if not all((source / name).is_file() and (source / name).stat().st_size > 0 for name in required):
            raise ValueError("Assets của Lecture 1 chưa đầy đủ.")
        target = self.jobs.bundle_dir("lecture1")
        with self.lock:
            if not all((target / name).is_file() and (target / name).stat().st_size > 0 for name in required):
                target.mkdir(parents=True, exist_ok=True)
                for name in required:
                    shutil.copy2(source / name, target / name)
            self._write(self._records())

    def validate(self, lecture_id):
        if lecture_id not in LECTURE_IDS:
            raise ValueError("Lecture không hợp lệ.")
        return lecture_id

    def list(self):
        with self.lock:
            records = self._records()
        rows = []
        for record in records:
            bundle_id = record["bundle_id"]
            root = self.jobs.bundle_dir(bundle_id)
            published = all((root / name).is_file() and (root / name).stat().st_size > 0 for name in ("lesson.json", "sources.json", "recap.mp4"))
            row = {"lecture_id": record["lecture_id"], "title": record["title"], "published": published}
            if published:
                try:
                    lesson = json.loads((root / "lesson.json").read_text(encoding="utf-8"))
                    lesson_title = str(lesson["title"]).strip()
                    checkpoints = lesson["checkpoints"]
                    if not lesson_title or not isinstance(checkpoints, list):
                        raise ValueError
                    row.update({"lesson_title": lesson_title, "checkpoint_count": len(checkpoints), "bundle_url": f"/learn/{bundle_id}"})
                except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
                    row["published"] = False
            if not row["published"]:
                row["checkpoint_count"] = 0
            rows.append(row)
        return rows


class UserStore:
    """Local-only display names for role-switching demos; this is not authentication."""

    def __init__(self, runtime_root):
        self.root = Path(runtime_root).resolve()
        self.path = self.root / "users.json"
        self.lock = threading.Lock()
        self.root.mkdir(parents=True, exist_ok=True)

    def _read(self):
        if not self.path.is_file():
            return [{"id": "demo-user", "name": "User demo"}]
        try:
            users = json.loads(self.path.read_text(encoding="utf-8"))
            return users if isinstance(users, list) else []
        except (OSError, ValueError, json.JSONDecodeError):
            return []

    def _write(self, users):
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(users, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, self.path)

    def list(self):
        with self.lock:
            users = self._read()
            if not users:
                users = [{"id": "demo-user", "name": "User demo"}]
                self._write(users)
            return users

    def get(self, user_id):
        return next((user for user in self.list() if user["id"] == user_id), None)

    def create(self, name):
        name = str(name or "").strip()
        if not 2 <= len(name) <= 40 or any(character in name for character in "<>&\r\n"):
            raise ValueError("Tên user cần 2–40 ký tự và không chứa ký tự đặc biệt.")
        with self.lock:
            users = self._read()
            user = {"id": f"user-{uuid.uuid4().hex[:12]}", "name": name}
            users.append(user)
            self._write(users)
            return user


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
        users = {item.get("user_id"): item.get("user_name", "User local") for item in events if item.get("user_id")}
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
            row = {
                "session_id": session_id,
                "event_count": len(session_events),
                "last_event_at": last_event["timestamp"],
                "completed": session_id in completion,
            }
            if session_id in completion:
                completed_event = completion[session_id]
                if isinstance(completed_event.get("score"), (int, float)):
                    row["score"] = completed_event["score"]
                if isinstance(completed_event.get("first_attempt_accuracy"), (int, float)):
                    row["first_attempt_accuracy"] = completed_event["first_attempt_accuracy"]
            session_rows.append(row)
        session_rows.sort(key=lambda row: (row["last_event_at"], row["session_id"]), reverse=True)
        user_rows = []
        for user_id, user_name in users.items():
            user_events = [event for event in events if event.get("user_id") == user_id]
            last_event = max(user_events, key=lambda event: event["timestamp"])
            user_sessions = {event["session_id"] for event in user_events}
            user_rows.append({
                "user_id": user_id, "user_name": user_name, "event_count": len(user_events),
                "last_event_at": last_event["timestamp"],
                "completed": any(session_id in completion for session_id in user_sessions),
            })
        user_rows.sort(key=lambda row: (row["last_event_at"], row["user_id"]), reverse=True)
        recent_events = []
        for event in sorted(events, key=lambda event: (event["timestamp"], event["session_id"]))[-20:]:
            row = {
                "session_id": event["session_id"], "timestamp": event["timestamp"], "event": event["event"],
                "checkpoint_id": event.get("checkpoint_id"), "is_correct": event.get("is_correct"),
            }
            if event.get("user_id"):
                row.update({"user_id": event["user_id"], "user_name": event.get("user_name", "User local")})
            recent_events.append(row)
        completed_scores = [item["score"] for item in completion.values() if isinstance(item.get("score"), (int, float))]
        return {
            "views": len(sessions), "completed_sessions": len(completion),
            "fast_completion_count": sum(item.get("needs_review") is True for item in completion.values()),
            "average_score": round(sum(completed_scores) / len(completed_scores), 1) if completed_scores else 0,
            "average_response_time_ms": round(sum(response_times) / len(response_times)) if response_times else 0,
            "average_completion_seconds": round(sum(item.get("completion_seconds", 0) for item in completion.values()) / len(completion)) if completion else 0,
            "checkpoints": rows,
            "misconceptions": [{"misconception_id": key[0], "label": key[1], "count": count} for key, count in misconceptions.most_common()],
            "users": user_rows[:20],
            "sessions": session_rows[:20],
            "recent_events": recent_events,
        }
