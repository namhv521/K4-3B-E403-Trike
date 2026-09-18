"""Entry point for the fullscreen interactive recap player."""

import argparse
import json
import os
import sys
from pathlib import Path


os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def load_bundle(asset_dir):
    asset_dir = Path(asset_dir)
    lesson_path = asset_dir / "lesson.json"
    video_path = asset_dir / "recap.mp4"
    audio_path = asset_dir / "narration.mp3"
    for path in (lesson_path, video_path, audio_path):
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Missing generated asset: {path.name}")
    try:
        lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("lesson.json is not valid JSON") from error
    if not isinstance(lesson.get("checkpoints"), list) or not lesson["checkpoints"]:
        raise ValueError("lesson.json checkpoints must not be empty")
    if not isinstance(lesson.get("duration_seconds"), (int, float)):
        raise ValueError("lesson.json duration_seconds is required")
    return lesson, video_path, audio_path


def application_root():
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def writable_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="Play a fullscreen interactive recap lesson")
    parser.add_argument("--assets", type=Path, default=application_root() / "assets")
    parser.add_argument("--windowed", action="store_true", help="Run in a resizable window for development")
    args = parser.parse_args()
    lesson, video_path, audio_path = load_bundle(args.assets)
    from player import InteractivePlayer
    InteractivePlayer(
        lesson, video_path, audio_path,
        writable_root() / "runtime-logs",
        fullscreen=not args.windowed,
    ).run()


if __name__ == "__main__":
    main()
