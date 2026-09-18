"""Local VLearn prototype server: static learner UI plus admin/job/telemetry APIs."""

import argparse
import cgi
import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from service import JobStore, TelemetryStore

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / "runtime"
GENERATOR = ROOT.parent / "video-generator"
JOBS = JobStore(RUNTIME)
TELEMETRY = TelemetryStore(RUNTIME / "telemetry")


class WebsiteHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".mjs": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8", ".mp4": "video/mp4"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Content-Security-Policy", "default-src 'self'; media-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; base-uri 'none'; frame-ancestors 'self'")
        super().end_headers()

    def log_message(self, format, *args):
        if os.getenv("VLEARN_HTTP_LOG") == "1":
            super().log_message(format, *args)

    def send_json(self, value, status=HTTPStatus.OK):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status, message):
        self.send_json({"error": message}, status)

    def _bundle_asset(self, path):
        parts = path.split("/")
        if len(parts) != 5 or parts[:3] != ["", "api", "bundles"] or parts[4] not in {"lesson.json", "sources.json", "recap.mp4"}:
            return None
        try:
            root = JOBS.bundle_dir(parts[3]).resolve()
        except ValueError:
            return None
        target = (root / parts[4]).resolve()
        return target if target.parent == root and target.is_file() else None

    def _serve_bundle_asset(self, target):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", self.guess_type(str(target)) or "application/octet-stream")
        self.send_header("Content-Length", str(target.stat().st_size))
        self.end_headers()
        with target.open("rb") as handle:
            self.copyfile(handle, self.wfile)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/admin":
            self.path = "/admin.html"
            return super().do_GET()
        if parsed.path.startswith("/learn/"):
            bundle_id = parsed.path.removeprefix("/learn/")
            try:
                JOBS.bundle_dir(bundle_id)
            except ValueError:
                return self.send_error_json(HTTPStatus.BAD_REQUEST, "Bundle id không hợp lệ.")
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", f"/?bundle={bundle_id}")
            self.end_headers()
            return
        asset = self._bundle_asset(parsed.path)
        if asset:
            return self._serve_bundle_asset(asset)
        if parsed.path.startswith("/api/admin/jobs/"):
            try:
                return self.send_json(JOBS.get(parsed.path.rsplit("/", 1)[-1]))
            except (FileNotFoundError, ValueError):
                return self.send_error_json(HTTPStatus.NOT_FOUND, "Không tìm thấy job.")
        if parsed.path == "/api/admin/analytics":
            return self.send_json(TELEMETRY.analytics(parse_qs(parsed.query).get("bundle_id", [""])[0]))
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/events":
            return self._post_event()
        if parsed.path == "/api/admin/jobs":
            return self._post_job()
        return self.send_error_json(HTTPStatus.NOT_FOUND, "Không tìm thấy API.")

    def _post_event(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 16_384:
                raise ValueError
            payload = json.loads(self.rfile.read(size))
            bundle_id = payload.pop("bundle_id", "")
            if not JOBS.bundle_dir(bundle_id).is_dir():
                raise ValueError
            return self.send_json({"accepted": True, "event": TELEMETRY.append(bundle_id, payload)}, HTTPStatus.ACCEPTED)
        except (ValueError, json.JSONDecodeError):
            return self.send_error_json(HTTPStatus.BAD_REQUEST, "Event không hợp lệ.")

    def _post_job(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 100 * 1024 * 1024:
                raise ValueError("Upload cần từ 1 byte đến 100 MB.")
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("Content-Type", "")})
            uploaded = form["files"] if "files" in form else []
            uploaded = uploaded if isinstance(uploaded, list) else [uploaded]
            files = [(item.filename, item.file.read()) for item in uploaded if item.filename and item.file]
            job = JOBS.create(form.getfirst("prompt", ""), files)
            JOBS.run_async(job["id"], GENERATOR)
            return self.send_json(job, HTTPStatus.ACCEPTED)
        except ValueError as error:
            return self.send_error_json(HTTPStatus.BAD_REQUEST, str(error))
        except Exception:
            return self.send_error_json(HTTPStatus.BAD_REQUEST, "Không thể nhận upload. Kiểm tra file và thử lại.")


def main():
    parser = argparse.ArgumentParser(description="Run the local VLearn admin and interactive-video prototype.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), WebsiteHandler)
    print(f"VLearn local admin: http://127.0.0.1:{args.port}/admin")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
