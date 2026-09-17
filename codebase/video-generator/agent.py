"""One-command agent for generating an interactive recap lesson."""

import argparse
import json
import os
import tempfile
from pathlib import Path

from extract_sources import extract_path
from generate_content import generate_lesson
from generate_images import generate_images
from generate_tts import generate_tts
from lesson_schema import validate_lesson
from openrouter_client import OpenRouterClient, redact
from render_video import render_video


def _write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _publish(staging, output):
    output.mkdir(parents=True, exist_ok=True)
    for item in staging.iterdir():
        os.replace(item, output / item.name)


def publish_fixture(fixture_path, output_dir, renderer=render_video):
    lesson = validate_lesson(json.loads(Path(fixture_path).read_text(encoding="utf-8")))
    lesson["generation"] = {"mode": "mock", "notice": "Fixture offline; OpenRouter was not called."}
    output_dir = Path(output_dir)
    with tempfile.TemporaryDirectory(dir=output_dir.parent if output_dir.parent.exists() else None) as folder:
        staging = Path(folder)
        _write_json(staging / "lesson.json", lesson)
        _write_json(staging / "sources.json", [])
        _write_json(staging / "ai-trace.json", {"ai_called": False, "mode": "mock"})
        (staging / "transcript.txt").write_text(lesson["narration"], encoding="utf-8")
        renderer(lesson, None, staging / "recap.mp4")
        _publish(staging, output_dir)
    return output_dir


def generate(input_path, prompt, output_dir):
    client = OpenRouterClient()
    traces = []

    def transcriber(path):
        text, trace = client.transcribe(path)
        traces.append(trace)
        return text

    records = extract_path(Path(input_path), transcriber=transcriber)
    lesson, content_traces = generate_lesson(records, prompt, client)
    traces.extend(content_traces)
    generate_images(lesson["scenes"], client, enabled=False)
    lesson["generation"] = {"mode": "openrouter", "images_enabled": False}
    output_dir = Path(output_dir)
    with tempfile.TemporaryDirectory(dir=output_dir.parent if output_dir.parent.exists() else None) as folder:
        staging = Path(folder)
        voice_path = staging / "narration.mp3"
        traces.append(generate_tts(lesson, client, voice_path))
        render_video(lesson, voice_path, staging / "recap.mp4")
        _write_json(staging / "lesson.json", lesson)
        _write_json(staging / "sources.json", records)
        _write_json(staging / "ai-trace.json", {"ai_called": True, "events": redact(traces)})
        (staging / "transcript.txt").write_text(lesson["narration"], encoding="utf-8")
        _publish(staging, output_dir)
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Generate an interactive recap video from lesson sources.")
    parser.add_argument("--input", help="File or folder containing source material")
    parser.add_argument("--prompt", default="Tạo video ôn tập 60-90 giây")
    parser.add_argument("--output", default="output")
    parser.add_argument("--fixture", help="Offline lesson JSON; explicitly marked mock")
    args = parser.parse_args()
    if args.fixture:
        publish_fixture(args.fixture, args.output)
    elif args.input:
        generate(args.input, args.prompt, args.output)
    else:
        parser.error("provide --input or --fixture")
    print(f"Generated lesson bundle: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
