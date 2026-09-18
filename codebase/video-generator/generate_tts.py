"""Generate Vietnamese narration with the free public Edge TTS service."""

import os
import subprocess
import sys
from pathlib import Path


def generate_tts(lesson, client, output_path, runner=subprocess.run):
    output_path = Path(output_path)
    command = [
        sys.executable, "-m", "edge_tts",
        "--voice", os.getenv("EDGE_TTS_VOICE", "vi-VN-HoaiMyNeural"),
        "--text", lesson["narration"],
        "--write-media", str(output_path),
    ]
    for attempt in range(2):
        result = runner(command, capture_output=True, text=True)
        if not result.returncode:
            break
        if attempt:
            raise RuntimeError(f"Edge TTS failed: {result.stderr[-500:]}")
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError("Edge TTS returned empty audio")
    return {"operation": "tts", "provider": "edge-tts", "voice": command[4]}
