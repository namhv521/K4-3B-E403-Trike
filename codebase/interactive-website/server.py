"""Static prototype server with a small, validated JSONL logging endpoint."""

import argparse
import json
import threading
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "runtime-logs"
MAX_BODY = 32 * 1024
WRITE_LOCK = threading.Lock()
ALLOWED_FIELDS = {
    "session_id", "timestamp", "event", "video_time", "checkpoint_id", "attempt_number",
    "selected_answer", "is_correct", "misconception_id", "misconception_label",
    "action_after_feedback", "response_time_ms", "score"
}


def parse_byte_range(value, size):
    if not value or not value.startswith("bytes=") or "," in value or size <= 0:
        raise ValueError("unsupported byte range")
    start_text, separator, end_text = value[6:].partition("-")
    if not separator:
        raise ValueError("invalid byte range")
    if start_text:
        start = int(start_text)
        end = int(end_text) if end_text else size - 1
    else:
        suffix = int(end_text)
        if suffix <= 0:
            raise ValueError("invalid byte range")
        start, end = max(0, size - suffix), size - 1
    if start < 0 or start >= size or end < start:
        raise ValueError("range is outside the file")
    return start, min(end, size - 1)


def sanitize_event(event):
    if not isinstance(event, dict):
        raise ValueError("event body must be an object")
    for required in ("session_id", "timestamp", "event"):
        if not isinstance(event.get(required), str) or not event[required].strip():
            raise ValueError(f"{required} is required")
    clean = {key: value for key, value in event.items() if key in ALLOWED_FIELDS}
    encoded = json.dumps(clean, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_BODY:
        raise ValueError("event is too large")
    return clean


def append_event(log_dir, event, now=None):
    clean = sanitize_event(event)
    now = now or datetime.now(timezone.utc)
    log_dir = Path(log_dir).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    path = (log_dir / f"{now:%Y-%m-%d}.jsonl").resolve()
    if log_dir not in path.parents:
        raise ValueError("invalid log path")
    line = json.dumps(clean, ensure_ascii=False, separators=(",", ":")) + "\n"
    with WRITE_LOCK, path.open("a", encoding="utf-8") as stream:
        stream.write(line)
    return path


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; media-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'")
        super().end_headers()

    def _json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/health":
            self._json(200, {"ok": True})
            return
        if self.headers.get("Range") and self._serve_video_range():
            return
        super().do_GET()

    def _serve_video_range(self):
        relative = unquote(urlsplit(self.path).path).lstrip("/")
        path = (ROOT / relative).resolve()
        if ROOT not in path.parents or path.suffix.lower() != ".mp4" or not path.is_file():
            return False
        size = path.stat().st_size
        try:
            start, end = parse_byte_range(self.headers["Range"], size)
        except (TypeError, ValueError):
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return True
        self.send_response(206)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        with path.open("rb") as stream:
            stream.seek(start)
            remaining = end - start + 1
            while remaining:
                chunk = stream.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)
        return True

    def do_POST(self):
        if self.path != "/api/logs":
            self._json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY:
                raise ValueError("request body is empty or too large")
            event = json.loads(self.rfile.read(length))
            append_event(LOG_DIR, event)
            self._json(201, {"saved": True})
        except (ValueError, json.JSONDecodeError) as error:
            self._json(400, {"error": str(error)})
        except OSError:
            self._json(500, {"error": "Log storage is not writable"})

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Interactive recap: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
