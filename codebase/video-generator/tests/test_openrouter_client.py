import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_images import generate_images
from openrouter_client import OpenRouterClient, redact


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url, headers, body))
        return self.responses.pop(0)


class OpenRouterClientTests(unittest.TestCase):
    def test_uses_ling_flash_free_as_default_text_model(self):
        previous_model = os.environ.pop("OPENROUTER_TEXT_MODEL", None)
        try:
            client = OpenRouterClient("secret", transport=FakeTransport([]))
        finally:
            if previous_model is not None:
                os.environ["OPENROUTER_TEXT_MODEL"] = previous_model

        self.assertEqual("inclusionai/ling-3.0-flash-fin:free", client.text_model)

    def test_chat_json_uses_bearer_and_parses_content(self):
        response = {"choices": [{"message": {"content": "```json\n{\"title\": \"Bài học\"}\n```"}}], "usage": {"cost": 0}}
        transport = FakeTransport([(200, {"content-type": "application/json"}, json.dumps(response).encode())])
        client = OpenRouterClient("secret", transport=transport)
        data, trace = client.chat_json([{"role": "user", "content": "Tạo bài"}], "lesson")
        self.assertEqual("Bài học", data["title"])
        self.assertEqual("Bearer secret", transport.calls[0][2]["Authorization"])
        self.assertEqual("lesson", trace["schema"])

    def test_rejects_malformed_model_json(self):
        response = {"choices": [{"message": {"content": "không phải json"}}]}
        client = OpenRouterClient("secret", transport=FakeTransport([(200, {}, json.dumps(response).encode())] * 3))
        with self.assertRaisesRegex(ValueError, "valid JSON"):
            client.chat_json([{"role": "user", "content": "x"}], "lesson")

    def test_chat_json_retries_a_malformed_free_model_response(self):
        malformed = {"choices": [{"message": {"content": None}}]}
        valid = {"model": "demo/free", "choices": [{"message": {"content": "{\"title\": \"Bài học\"}"}}]}
        transport = FakeTransport([
            (200, {}, json.dumps(malformed).encode()),
            (200, {}, json.dumps(valid).encode()),
        ])

        data, trace = OpenRouterClient("secret", transport=transport).chat_json([{"role": "user", "content": "x"}], "lesson")

        self.assertEqual("Bài học", data["title"])
        self.assertEqual("demo/free", trace["model"])
        self.assertEqual(2, len(transport.calls))

    def test_free_tts_is_discovered_and_written(self):
        models = {"data": [{"id": "demo/free-tts", "pricing": {"input_audio": "0", "output_audio": "0"}}]}
        transport = FakeTransport([
            (200, {}, json.dumps(models).encode()),
            (200, {"content-type": "audio/mpeg", "x-generation-id": "g1"}, b"mp3-data"),
        ])
        client = OpenRouterClient("secret", transport=transport)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "voice.mp3")
            trace = client.synthesize_free("Xin chào", path)
            self.assertEqual(b"mp3-data", path.read_bytes())
        self.assertEqual("demo/free-tts", trace["model"])

    def test_paid_only_tts_fails(self):
        models = {"data": [{"id": "paid/tts", "pricing": {"input_audio": "0.01"}}]}
        client = OpenRouterClient("secret", transport=FakeTransport([(200, {}, json.dumps(models).encode())]))
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "free/public TTS"):
                client.synthesize_free("Xin chào", Path(folder, "voice.mp3"))

    def test_redact_removes_secret_fields(self):
        self.assertEqual({"api_key": "[REDACTED]", "nested": {"token": "[REDACTED]"}}, redact({"api_key": "x", "nested": {"token": "y"}}))

    def test_disabled_image_generation_never_calls_client(self):
        result = generate_images([], object(), enabled=False)
        self.assertEqual({"enabled": False, "images": []}, result)


if __name__ == "__main__":
    unittest.main()
