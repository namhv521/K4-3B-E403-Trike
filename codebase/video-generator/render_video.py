"""Render grounded recap lessons through Remotion, with an FFmpeg fallback."""

import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1280, 720
REMOTION_ROOT = Path(__file__).resolve().parent / "remotion-recap"


def _find_browser():
    env_browser = os.getenv("REMOTION_BROWSER_EXECUTABLE") or os.getenv("CHROME_BIN")
    if env_browser and Path(env_browser).is_file():
        return str(Path(env_browser))
    candidates = [
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
        Path(os.getenv("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe",
        Path(os.getenv("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


def remotion_command(lesson, narration_path, output_path, public_narration_path=None):
    """Build the generic Remotion command without putting lesson text in logs."""
    output_path = Path(output_path)
    props = {"lesson": lesson, "narrationPath": public_narration_path or (Path(narration_path).name if narration_path else None)}
    cli = REMOTION_ROOT / "node_modules" / "@remotion" / "cli" / "remotion-cli.js"
    command = [
        "node", str(cli), "render", "src/index.ts", "VLearnRecap", str(output_path),
        "--props", json.dumps(props, ensure_ascii=False),
    ]
    browser = _find_browser()
    if browser:
        command.extend(["--browser-executable", browser])
    return command


def _font(size, bold=False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    candidates = [Path("C:/Windows/Fonts") / name, Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    path = next((item for item in candidates if item.exists()), None)
    return ImageFont.truetype(str(path), size) if path else ImageFont.load_default()


def _frame(scene, index, count, path):
    image = Image.new("RGB", (WIDTH, HEIGHT), "#091426")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((58, 54, WIDTH - 58, HEIGHT - 54), radius=34, fill="#102541", outline="#2d5875", width=2)
    draw.rectangle((58, 54, 74, HEIGHT - 54), fill="#35d6b1")
    draw.text((112, 98), f"Concept {index + 1}/{count}", font=_font(25, True), fill="#64e3c4")
    draw.text((112, 154), scene["title"], font=_font(58, True), fill="#f5f1e8")
    y = 250
    for line in textwrap.wrap(scene.get("body", ""), width=48):
        draw.text((112, y), line, font=_font(34), fill="#b9c9d9")
        y += 52
    draw.text((112, HEIGHT - 116), "Recap Studio · nguồn được truy vết", font=_font(22), fill="#7390a8")
    image.save(path)


def _render_ffmpeg(lesson, narration_path, output_path):
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is required to render video")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scenes = lesson["scenes"]
    duration = float(lesson["duration_seconds"])
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        concat_lines = []
        for index, scene in enumerate(scenes):
            frame = root / f"scene-{index:03d}.png"
            _frame(scene, index, len(scenes), frame)
            scene_duration = max(0.5, float(scene.get("end", duration)) - float(scene.get("start", 0)))
            concat_lines.extend([f"file '{frame.as_posix()}'", f"duration {scene_duration}"])
        concat_lines.append(f"file '{frame.as_posix()}'")
        concat_file = root / "frames.txt"
        concat_file.write_text("\n".join(concat_lines), encoding="utf-8")
        command = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file)]
        if narration_path:
            command += ["-i", str(narration_path), "-af", "apad"]
        else:
            command += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        command += [
            "-t", str(duration), "-vf", "tpad=stop_mode=clone:stop_duration=10", "-r", "24", "-c:v", "libx264", "-preset", "ultrafast",
            "-tune", "stillimage", "-crf", "28", "-pix_fmt", "yuv420p", "-c:a", "aac",
            str(output_path)
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(f"FFmpeg render failed: {result.stderr[-800:]}")
    return output_path


def render_video(lesson, narration_path, output_path):
    """Render with Remotion when requested; keep the tested FFmpeg fallback explicit."""
    renderer = os.getenv("VLEARN_RENDERER", "ffmpeg").lower()
    if renderer == "remotion":
        if not (REMOTION_ROOT / "node_modules" / "@remotion" / "cli" / "remotion-cli.js").is_file() or shutil.which("node") is None:
            raise RuntimeError("Remotion renderer is not installed; run npm install in video-generator/remotion-recap.")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        public_audio = None
        temporary_audio = None
        if narration_path:
            public_root = REMOTION_ROOT / "public" / "runtime"
            public_root.mkdir(parents=True, exist_ok=True)
            temporary_audio = public_root / f"narration-{uuid.uuid4().hex}.mp3"
            shutil.copy2(narration_path, temporary_audio)
            public_audio = f"runtime/{temporary_audio.name}"
        command = remotion_command(lesson, narration_path, output_path, public_audio)
        try:
            result = subprocess.run(command, cwd=REMOTION_ROOT, capture_output=True, text=True)
        finally:
            if temporary_audio:
                temporary_audio.unlink(missing_ok=True)
        if result.returncode or not output_path.is_file() or output_path.stat().st_size == 0:
            raise RuntimeError(f"Remotion render failed: {result.stderr[-800:]}")
        return output_path
    if renderer != "ffmpeg":
        raise RuntimeError("VLEARN_RENDERER must be remotion or ffmpeg.")
    return _render_ffmpeg(lesson, narration_path, output_path)
