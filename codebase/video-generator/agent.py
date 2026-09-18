"""One-command agent for generating an interactive recap lesson."""

import argparse
import json
import os
import tempfile
from pathlib import Path

from extract_sources import extract_path
from generate_content import generate_lesson, source_catalog
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


def require_lesson_sources(records):
    templates = {"mau-kich-ban", "readme", "khung-hinh"}
    content = [record for record in records if Path(record["source"]).stem.lower() not in templates]
    if not content:
        raise ValueError("Input chỉ chứa file mẫu; hãy thêm nội dung bài giảng, slide, PDF, audio hoặc video.")
    return content


def fixture_source_catalog(lesson):
    """Replace fixture references with non-sensitive, explicitly mock citations."""
    raw_refs = []
    for item in [*lesson["scenes"], *lesson["checkpoints"]]:
        raw_refs.extend(item["source_refs"])
    mapping = {
        raw_ref: f"fixture-{index + 1}"
        for index, raw_ref in enumerate(dict.fromkeys(raw_refs))
    }
    for item in [*lesson["scenes"], *lesson["checkpoints"]]:
        item["source_refs"] = [mapping[raw_ref] for raw_ref in item["source_refs"]]
    return [
        {"ref": ref, "source": "Mock fixture", "locator": f"fixture reference {index + 1}"}
        for index, ref in enumerate(mapping.values())
    ]


def publish_fixture(fixture_path, output_dir, renderer=render_video, tts_generator=generate_tts):
    lesson = validate_lesson(json.loads(Path(fixture_path).read_text(encoding="utf-8")))
    sources = fixture_source_catalog(lesson)
    lesson["generation"] = {"mode": "mock", "notice": "Fixture content; OpenRouter was not called."}
    output_dir = Path(output_dir)
    with tempfile.TemporaryDirectory(dir=output_dir.parent if output_dir.parent.exists() else None) as folder:
        staging = Path(folder)
        _write_json(staging / "lesson.json", lesson)
        _write_json(staging / "sources.json", sources)
        voice_path = staging / "narration.mp3"
        tts_trace = tts_generator(lesson, None, voice_path)
        _write_json(staging / "ai-trace.json", {"ai_called": False, "mode": "mock", "tts": tts_trace})
        (staging / "transcript.txt").write_text(lesson["narration"], encoding="utf-8")
        renderer(lesson, voice_path, staging / "recap.mp4")
        _publish(staging, output_dir)
    return output_dir


def generate(input_path, prompt, output_dir):
    client = None
    traces = []

    def get_client():
        nonlocal client
        if client is None:
            client = OpenRouterClient()
        return client

    def transcriber(path):
        text, trace = get_client().transcribe(path)
        traces.append(trace)
        return text

    records = require_lesson_sources(extract_path(Path(input_path), transcriber=transcriber))
    client = get_client()
    lesson, content_traces = generate_lesson(records, prompt, client)
    traces.extend(content_traces)
    generate_images(lesson["scenes"], client, enabled=False)
    lesson["generation"] = {"mode": "openrouter", "images_enabled": False}
    output_dir = Path(output_dir)
    with tempfile.TemporaryDirectory(dir=output_dir.parent if output_dir.parent.exists() else None) as folder:
        staging = Path(folder)
        voice_path = staging / "narration.mp3"
        traces.append(generate_tts(lesson, client, voice_path))
        previous_renderer = os.environ.get("VLEARN_RENDERER")
        os.environ.setdefault("VLEARN_RENDERER", "remotion")
        try:
            render_video(lesson, voice_path, staging / "recap.mp4")
        finally:
            if previous_renderer is None:
                os.environ.pop("VLEARN_RENDERER", None)
        _write_json(staging / "lesson.json", lesson)
        _write_json(staging / "sources.json", source_catalog(records))
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
