"""Minimal OpenRouter client used by the video agent."""

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = "https://openrouter.ai/api/v1"
SECRET_KEYS = {"api_key", "authorization", "token", "secret"}


def redact(value):
    if isinstance(value, dict):
        return {key: "[REDACTED]" if key.lower() in SECRET_KEYS else redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def _default_transport(method, url, headers, body):
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


def _is_free(model):
    if str(model.get("id", "")).endswith(":free"):
        return True
    pricing = model.get("pricing") or {}
    if isinstance(pricing, dict):
        values = [value for value in pricing.values() if value is not None]
        return bool(values) and all(float(value) == 0 for value in values)
    if isinstance(pricing, list):
        return bool(pricing) and all(float(item.get("cost_usd", 1)) == 0 for item in pricing)
    return False


class OpenRouterClient:
    def __init__(self, api_key=None, transport=None, text_model=None, transcription_model=None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")
        self.transport = transport or _default_transport
        self.text_model = text_model or os.getenv("OPENROUTER_TEXT_MODEL", "openrouter/free")
        self.transcription_model = transcription_model or os.getenv("OPENROUTER_TRANSCRIPTION_MODEL", "openai/whisper-1")

    def _request(self, method, path, payload=None):
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        last_error = None
        for attempt in range(2):
            status, response_headers, raw = self.transport(method, f"{BASE_URL}{path}", headers, body)
            if 200 <= status < 300:
                return response_headers, raw
            last_error = RuntimeError(f"OpenRouter returned HTTP {status}: {raw[:300].decode('utf-8', 'replace')}")
            if status < 500 or attempt == 1:
                break
            time.sleep(0.2)
        raise last_error

    def _request_json(self, method, path, payload=None):
        _, raw = self._request(method, path, payload)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError("OpenRouter returned invalid JSON") from error

    def chat_json(self, messages, schema_name):
        started = time.time()
        response = self._request_json("POST", "/chat/completions", {
            "model": self.text_model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        })
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise ValueError("Model did not return valid JSON")
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError as error:
            raise ValueError("Model did not return valid JSON") from error
        return data, {
            "operation": "chat_json",
            "schema": schema_name,
            "model": response.get("model", self.text_model),
            "duration_ms": round((time.time() - started) * 1000),
            "usage": response.get("usage", {}),
        }

    def transcribe(self, path: Path):
        path = Path(path)
        response = self._request_json("POST", "/audio/transcriptions", {
            "model": self.transcription_model,
            "input_audio": {"data": base64.b64encode(path.read_bytes()).decode("ascii"), "format": path.suffix.lstrip(".") or "wav"},
            "response_format": "verbose_json",
        })
        return response.get("text", ""), {"operation": "transcription", "model": self.transcription_model, "usage": response.get("usage", {})}

    def synthesize_free(self, text: str, output_path: Path):
        models = self._request_json("GET", "/models?output_modalities=speech")
        model = next((item for item in models.get("data", []) if _is_free(item)), None)
        if model is None:
            raise RuntimeError("No free/public TTS model is currently available on OpenRouter")
        headers, raw = self._request("POST", "/audio/speech", {
            "model": model["id"],
            "input": text,
            "voice": os.getenv("OPENROUTER_TTS_VOICE", "alloy"),
            "response_format": "mp3",
        })
        Path(output_path).write_bytes(raw)
        return {"operation": "tts", "model": model["id"], "generation_id": headers.get("x-generation-id") or headers.get("X-Generation-Id")}
