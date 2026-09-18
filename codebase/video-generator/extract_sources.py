"""Extract traceable text records from common lesson source files."""

import re
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader


TEXT_EXTENSIONS = {".md", ".txt"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv"}


def _record(text, source, locator):
    return {"text": " ".join(text.split()), "source": str(source), "locator": locator}


def _extract_text(path):
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if line.strip():
            records.append(_record(line, path, f"line:{line_number}"))
    return records


def _extract_pptx(path):
    records = []
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        names.sort(key=lambda name: int(re.search(r"\d+", Path(name).stem).group()))
        for slide_number, name in enumerate(names, 1):
            root = ElementTree.fromstring(archive.read(name))
            text = " ".join(node.text or "" for node in root.iter() if node.tag.endswith("}t"))
            if text.strip():
                records.append(_record(text, path, f"slide:{slide_number}"))
    return records


def _extract_docx(path):
    records = []
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    for paragraph in root.iter():
        if not paragraph.tag.endswith("}p"):
            continue
        text = "".join(node.text or "" for node in paragraph.iter() if node.tag.endswith("}t"))
        if text.strip():
            records.append(_record(text, path, f"paragraph:{len(records) + 1}"))
    return records


def _extract_pdf(path):
    records = []
    for page_number, page in enumerate(PdfReader(str(path)).pages, 1):
        text = page.extract_text() or ""
        if text.strip():
            records.append(_record(text, path, f"page:{page_number}"))
    return records


def _transcribe_media(path, transcriber):
    if transcriber is None:
        raise ValueError(f"A transcriber is required for {path.suffix} files")
    if path.suffix.lower() in AUDIO_EXTENSIONS:
        result = transcriber(path)
    else:
        with tempfile.TemporaryDirectory() as folder:
            audio_path = Path(folder, "audio.wav")
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", str(audio_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            result = transcriber(audio_path)
    text = result[0] if isinstance(result, tuple) else result
    return [_record(text, path, "audio:full")]


def extract_path(path: Path, transcriber=None) -> list[dict]:
    path = Path(path)
    if path.is_dir():
        records = []
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            try:
                records.extend(extract_path(child, transcriber))
            except ValueError as error:
                if "Unsupported" not in str(error):
                    raise
        if not records:
            raise ValueError(f"No supported lesson files found in {path}")
        return records
    if not path.is_file():
        raise ValueError(f"Input does not exist: {path}")
    extension = path.suffix.lower()
    if extension in TEXT_EXTENSIONS:
        return _extract_text(path)
    if extension == ".pptx":
        return _extract_pptx(path)
    if extension == ".docx":
        return _extract_docx(path)
    if extension == ".pdf":
        return _extract_pdf(path)
    if extension in AUDIO_EXTENSIONS | VIDEO_EXTENSIONS:
        return _transcribe_media(path, transcriber)
    raise ValueError(f"Unsupported lesson file: {path.name}")
