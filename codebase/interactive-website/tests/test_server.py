import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

import server
from service import JobStore, LectureStore, TelemetryStore, UserStore


class ServerRangeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = TemporaryDirectory()
        cls.root = Path(cls.temp_dir.name)
        cls.runtime = cls.root / "runtime"
        cls.runtime.mkdir()
        cls.assets = cls.root / "assets"
        cls.assets.mkdir()
        (cls.assets / "lesson.json").write_text(
            json.dumps({"title": "Test Lecture", "checkpoints": [{"id": "cp1", "time": 20}]}),
            encoding="utf-8",
        )
        (cls.assets / "sources.json").write_text("[]", encoding="utf-8")
        cls.mp4_bytes = b"0123456789ABCDEF" * 64  # 1024 bytes
        (cls.assets / "recap.mp4").write_bytes(cls.mp4_bytes)

        server.ROOT = cls.root
        server.RUNTIME = cls.runtime
        server.JOBS = JobStore(cls.runtime)
        server.LECTURES = LectureStore(cls.runtime, server.JOBS)
        server.USERS = UserStore(cls.runtime)
        server.TELEMETRY = TelemetryStore(cls.runtime / "telemetry")

        server.LECTURES.ensure_lecture_one(cls.assets)

        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.WebsiteHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.temp_dir.cleanup()

    def _request(self, method, path, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(method, path, headers=headers or {})
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp.status, dict(resp.getheaders()), body

    def test_full_video_request_returns_accept_ranges_header(self):
        status, headers, body = self._request("GET", "/api/bundles/lecture1/recap.mp4")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Accept-Ranges"), "bytes")
        self.assertEqual(headers.get("Content-Length"), str(len(self.mp4_bytes)))
        self.assertEqual(body, self.mp4_bytes)

    def test_byte_range_request_returns_206_partial_content(self):
        status, headers, body = self._request("GET", "/api/bundles/lecture1/recap.mp4", {"Range": "bytes=10-19"})
        self.assertEqual(status, 206)
        self.assertEqual(headers.get("Accept-Ranges"), "bytes")
        self.assertEqual(headers.get("Content-Range"), f"bytes 10-19/{len(self.mp4_bytes)}")
        self.assertEqual(headers.get("Content-Length"), "10")
        self.assertEqual(body, self.mp4_bytes[10:20])

    def test_start_open_ended_range_request(self):
        status, headers, body = self._request("GET", "/api/bundles/lecture1/recap.mp4", {"Range": "bytes=100-"})
        self.assertEqual(status, 206)
        self.assertEqual(headers.get("Content-Range"), f"bytes 100-{len(self.mp4_bytes)-1}/{len(self.mp4_bytes)}")
        self.assertEqual(body, self.mp4_bytes[100:])

    def test_suffix_range_request(self):
        status, headers, body = self._request("GET", "/api/bundles/lecture1/recap.mp4", {"Range": "bytes=-50"})
        self.assertEqual(status, 206)
        self.assertEqual(headers.get("Content-Range"), f"bytes {len(self.mp4_bytes)-50}-{len(self.mp4_bytes)-1}/{len(self.mp4_bytes)}")
        self.assertEqual(body, self.mp4_bytes[-50:])

    def test_out_of_bounds_range_request_returns_416(self):
        status, headers, body = self._request("GET", "/api/bundles/lecture1/recap.mp4", {"Range": "bytes=5000-6000"})
        self.assertEqual(status, 416)
        self.assertEqual(headers.get("Content-Range"), f"bytes */{len(self.mp4_bytes)}")
        self.assertEqual(body, b"")

    def test_head_request_with_range_returns_headers_and_no_body(self):
        status, headers, body = self._request("HEAD", "/api/bundles/lecture1/recap.mp4", {"Range": "bytes=0-9"})
        self.assertEqual(status, 206)
        self.assertEqual(headers.get("Content-Length"), "10")
        self.assertEqual(headers.get("Content-Range"), f"bytes 0-9/{len(self.mp4_bytes)}")
        self.assertEqual(body, b"")

    def test_static_asset_range_request(self):
        status, headers, body = self._request("GET", "/assets/recap.mp4", {"Range": "bytes=0-15"})
        self.assertEqual(status, 206)
        self.assertEqual(headers.get("Content-Range"), f"bytes 0-15/{len(self.mp4_bytes)}")
        self.assertEqual(body, self.mp4_bytes[:16])