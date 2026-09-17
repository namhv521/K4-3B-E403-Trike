import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from extract_sources import extract_path


class ExtractSourceTests(unittest.TestCase):
    def test_reads_text_with_line_locator(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "lesson.md")
            path.write_text("Dòng một\n\nDòng hai", encoding="utf-8")
            records = extract_path(path)
        self.assertEqual(["Dòng một", "Dòng hai"], [item["text"] for item in records])
        self.assertEqual("line:1", records[0]["locator"])

    def test_reads_pptx_slide_text(self):
        xml = '<p:sld xmlns:p="p" xmlns:a="a"><a:t>Khái niệm AI</a:t><a:t>Ví dụ</a:t></p:sld>'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "lesson.pptx")
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", xml)
            records = extract_path(path)
        self.assertEqual("Khái niệm AI Ví dụ", records[0]["text"])
        self.assertEqual("slide:1", records[0]["locator"])

    def test_routes_audio_to_transcriber(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "lesson.mp3")
            path.write_bytes(b"audio")
            records = extract_path(path, transcriber=lambda item: f"Phiên âm {item.name}")
        self.assertEqual("Phiên âm lesson.mp3", records[0]["text"])
        self.assertEqual("audio:full", records[0]["locator"])

    def test_rejects_unsupported_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "lesson.exe")
            path.write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                extract_path(path)


if __name__ == "__main__":
    unittest.main()
