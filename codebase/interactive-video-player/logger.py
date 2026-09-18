"""Append-only, allowlisted JSONL logging for learning events."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path


LOCK = threading.Lock()
ALLOWED_FIELDS = {
    "session_id", "timestamp", "event", "video_time", "checkpoint_id",
    "attempt_number", "selected_answer", "is_correct", "misconception_id",
    "misconception_label", "action_after_feedback", "response_time_ms", "score",
}


def append_event(log_dir, event, now=None):
    for field in ("session_id", "timestamp", "event"):
        if not isinstance(event.get(field), str) or not event[field].strip():
            raise ValueError(f"{field} is required")
    clean = {key: value for key, value in event.items() if key in ALLOWED_FIELDS}
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    now = now or datetime.now(timezone.utc)
    path = log_dir / f"{now:%Y-%m-%d}.jsonl"
    with LOCK, path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(clean, ensure_ascii=False, separators=(",", ":")) + "\n")
    return path
