"""Local VLearn prototype server: static learner UI plus admin/job/telemetry APIs."""

import argparse
import cgi
import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from service import JobStore, LectureStore, TelemetryStore, UserStore

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / "runtime"
GENERATOR = ROOT.parent / "video-generator"
JOBS = JobStore(RUNTIME)
LECTURES = LectureStore(RUNTIME, JOBS)
USERS = UserStore(RUNTIME)
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

    def _parse_range(self, range_header, file_size):
        if not range_header or not range_header.strip().startswith("bytes="):
            return None
        spec = range_header.strip()[6:].split(",")[0].strip()
        if "-" not in spec:
            return None
        start_str, end_str = spec.split("-", 1)
        try:
            if not start_str:
                suffix = int(end_str)
                if suffix <= 0:
                    return "invalid"
                start = max(0, file_size - suffix)
                end = file_size - 1
            elif not end_str:
                start = int(start_str)
                end = file_size - 1
            else:
                start = int(start_str)
                end = int(end_str)
            if start < 0 or start > end or end >= file_size:
                return "unsatisfiable"
            return start, end
        except ValueError:
            return "invalid"

    def _serve_file(self, target, content_type=None, is_head=False):
        try:
            file_size = target.stat().st_size
        except OSError:
            self.send_error_json(HTTPStatus.NOT_FOUND, "File không tồn tại.")
            return

        ctype = content_type or self.guess_type(str(target)) or "application/octet-stream"
        range_header = self.headers.get("Range")
        parsed_range = self._parse_range(range_header, file_size)

        if parsed_range == "unsatisfiable":
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header("Content-Range", f"bytes */{file_size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if isinstance(parsed_range, tuple):
            start, end = parsed_range
            content_length = end - start + 1
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(content_length))
            self.end_headers()
            if not is_head:
                try:
                    with target.open("rb") as handle:
                        handle.seek(start)
                        remaining = content_length
                        chunk_size = 64 * 1024
                        while remaining > 0:
                            chunk = handle.read(min(chunk_size, remaining))
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            remaining -= len(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(file_size))
        self.end_headers()
        if not is_head:
            try:
                with target.open("rb") as handle:
                    self.copyfile(handle, self.wfile)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def _serve_bundle_asset(self, target, is_head=False):
        return self._serve_file(target, is_head=is_head)

    def do_HEAD(self):
        parsed = urlparse(self.path)
        asset = self._bundle_asset(parsed.path)
        if asset:
            return self._serve_bundle_asset(asset, is_head=True)
        target = Path(self.translate_path(self.path)).resolve()
        if target.is_file() and target.is_relative_to(ROOT):
            return self._serve_file(target, is_head=True)
        return super().do_HEAD()

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
        if parsed.path == "/api/admin/bundles":
            return self.send_json(JOBS.list_published_bundles())
        if parsed.path == "/api/lectures":
            return self.send_json(LECTURES.list())
        if parsed.path == "/api/users":
            return self.send_json(USERS.list())
        if parsed.path == "/api/admin/analytics":
            return self.send_json(TELEMETRY.analytics(parse_qs(parsed.query).get("bundle_id", [""])[0]))
        target = Path(self.translate_path(self.path)).resolve()
        if target.is_file() and target.is_relative_to(ROOT):
            return self._serve_file(target)
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/events":
            return self._post_event()
        if parsed.path == "/api/admin/jobs":
            return self._post_job()
        if parsed.path == "/api/admin/users":
            return self._post_user()
        return self.send_error_json(HTTPStatus.NOT_FOUND, "Không tìm thấy API.")

    def _post_event(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 16_384:
                raise ValueError
            payload = json.loads(self.rfile.read(size))
            bundle_id = payload.pop("bundle_id", "")
            user = USERS.get(payload.get("user_id", ""))
            bundle_root = JOBS.bundle_dir(bundle_id)
            if not all((bundle_root / name).is_file() and (bundle_root / name).stat().st_size > 0 for name in ("lesson.json", "sources.json", "recap.mp4")):
                raise ValueError
            if not user:
                raise ValueError
            payload["user_id"] = user["id"]
            payload["user_name"] = user["name"]
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
            lecture_id = LECTURES.validate(form.getfirst("lecture_id", ""))
            job = JOBS.create(form.getfirst("prompt", ""), files, lecture_id)
            JOBS.run_async(job["id"], GENERATOR)
            return self.send_json(job, HTTPStatus.ACCEPTED)
        except ValueError as error:
            return self.send_error_json(HTTPStatus.BAD_REQUEST, str(error))
        except Exception:
            return self.send_error_json(HTTPStatus.BAD_REQUEST, "Không thể nhận upload. Kiểm tra file và thử lại.")

    def _post_user(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 4_096:
                raise ValueError("Tên user không hợp lệ.")
            payload = json.loads(self.rfile.read(size))
            return self.send_json(USERS.create(payload.get("name", "")), HTTPStatus.CREATED)
        except (ValueError, json.JSONDecodeError):
            return self.send_error_json(HTTPStatus.BAD_REQUEST, "Tên user không hợp lệ.")


def main():
    parser = argparse.ArgumentParser(description="Run the local VLearn admin and interactive-video prototype.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    LECTURES.ensure_lecture_one(ROOT / "assets")
    USERS.list()
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
