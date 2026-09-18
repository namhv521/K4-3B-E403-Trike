"""Generate Vietnamese narration with the free public Edge TTS service."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def generate_tts(lesson, client, output_path, runner=subprocess.run, aligner=subprocess.run):
    output_path = Path(output_path)
    duration = lesson.get("duration_seconds")
    temporary = None
    media_path = output_path
    if isinstance(duration, (int, float)) and duration > 0:
        handle = tempfile.NamedTemporaryFile(dir=output_path.parent, suffix=output_path.suffix, delete=False)
        handle.close()
        temporary = Path(handle.name)
        media_path = temporary
    command = [
        sys.executable, "-m", "edge_tts",
        "--voice", os.getenv("EDGE_TTS_VOICE", "vi-VN-HoaiMyNeural"),
        "--text", lesson["narration"],
        "--write-media", str(media_path),
    ]
    try:
        for attempt in range(2):
            result = runner(command, capture_output=True, text=True)
            if not result.returncode:
                break
            if attempt:
                raise RuntimeError(f"Edge TTS failed: {result.stderr[-500:]}")
        if not media_path.is_file() or media_path.stat().st_size == 0:
            raise RuntimeError("Edge TTS returned empty audio")
        trace = {"operation": "tts", "provider": "edge-tts", "voice": command[4]}
        if temporary:
            align_command = [
                "ffmpeg", "-y", "-i", str(temporary), "-af", "apad",
                "-t", str(duration), "-c:a", "libmp3lame", str(output_path),
            ]
            result = aligner(align_command, capture_output=True, text=True)
            if result.returncode or not output_path.is_file() or output_path.stat().st_size == 0:
                raise RuntimeError(f"FFmpeg audio alignment failed: {result.stderr[-500:]}")
            trace.update({"alignment": "ffmpeg-apad", "duration_seconds": duration})
        return trace
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
