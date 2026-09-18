import json
import re
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_content import generate_lesson, source_catalog
from test_lesson_schema import lesson


class FakeClient:
    def __init__(self, digest_text="ý chính"):
        self.calls = []
        self.digest_text = digest_text

    def chat_json(self, messages, schema):
        self.calls.append((messages, schema))
        if schema == "source_digest_v1":
            return {"facts": [self.digest_text], "source_refs": ["source"]}, {"schema": schema}
        result = lesson()
        refs = json.loads(re.search(r"ALLOWED_SOURCE_REFS:\n(\[.*?\])\nSOURCE_DIGESTS", messages[1]["content"], re.DOTALL).group(1))
        for scene in result["scenes"]:
            scene["source_refs"] = [refs[0]]
        for checkpoint in result["checkpoints"]:
            checkpoint["source_refs"] = [refs[0]]
        return result, {"schema": schema}


class ContentTests(unittest.TestCase):
    def test_multiple_source_batches_are_summarized_before_lesson(self):
        client = FakeClient()
        records = [
            {"text": "A" * 20, "source": "a.md", "locator": "line:1"},
            {"text": "B" * 20, "source": "b.md", "locator": "line:1"},
        ]
        _, traces = generate_lesson(records, "Tổng hợp", client, batch_chars=100)
        self.assertEqual(["source_digest_v1", "source_digest_v1", "interactive_lesson_v2"], [call[1] for call in client.calls])
        self.assertEqual(3, len(traces))

    def test_digest_reduction_keeps_final_request_inside_budget(self):
        client = FakeClient(digest_text="x" * 30)
        records = [
            {"text": str(index) * 20, "source": f"{index}.md", "locator": "line:1"}
            for index in range(8)
        ]
        generate_lesson(records, "Tổng hợp", client, batch_chars=100, digest_chars=220)
        final_messages = next(messages for messages, schema in client.calls if schema == "interactive_lesson_v2")
        final_payload = final_messages[1]["content"].split("SOURCE_DIGESTS:\n", 1)[1]
        self.assertLessEqual(len(final_payload), 220)

    def test_oversized_source_record_is_split_before_digest_calls(self):
        client = FakeClient()
        records = [{"text": "kiến thức " * 1000, "source": "audio.mp3", "locator": "audio:full"}]
        generate_lesson(records, "Tổng hợp", client, batch_chars=500)
        digest_payloads = [
            messages[1]["content"] for messages, schema in client.calls
            if schema == "source_digest_v1"
        ]
        self.assertGreater(len(digest_payloads), 1)
        self.assertTrue(all(len(payload) <= 500 for payload in digest_payloads))
        self.assertTrue(any("source_ref" in payload for payload in digest_payloads))

    def test_catalog_is_text_free_and_stable(self):
        records = [{"text": "Nội dung riêng tư", "source": r"C:\secret\lesson.md", "locator": "line:2"}]
        catalog = source_catalog(records)
        self.assertEqual("lesson.md", catalog[0]["source"])
        self.assertNotIn("text", catalog[0])
        self.assertTrue(catalog[0]["ref"].startswith("src-"))

    def test_absolute_extractor_paths_map_to_the_published_source_catalog(self):
        client = FakeClient()
        records = [{"text": "AI là lĩnh vực rộng.", "source": r"C:\runtime\jobs\job-1\input\lesson.md", "locator": "line:1"}]

        lesson_result, _ = generate_lesson(records, "Tổng hợp", client)

        self.assertTrue(lesson_result["scenes"][0]["source_refs"][0].startswith("src-"))

    def test_rejects_lesson_citation_that_is_not_in_source_catalog(self):
        class UngroundedClient(FakeClient):
            def chat_json(self, messages, schema):
                value, trace = super().chat_json(messages, schema)
                if schema == "interactive_lesson_v2":
                    value["checkpoints"][0]["source_refs"] = ["src-invented"]
                return value, trace

        client = UngroundedClient()
        records = [{"text": "AI là lĩnh vực rộng.", "source": "lesson.md", "locator": "line:1"}]
        with self.assertRaisesRegex(ValueError, "unsupported source references"):
            generate_lesson(records, "Tổng hợp", client)

    def test_repairs_a_parseable_lesson_that_is_missing_a_required_scene_field(self):
        class RepairingClient(FakeClient):
            def __init__(self):
                super().__init__()
                self.lesson_attempts = 0

            def chat_json(self, messages, schema):
                value, trace = super().chat_json(messages, schema)
                if schema == "interactive_lesson_v2":
                    self.lesson_attempts += 1
                    if self.lesson_attempts == 1:
                        value = deepcopy(value)
                        value["scenes"][0].pop("title")
                return value, trace

        client = RepairingClient()
        records = [{"text": "AI là lĩnh vực rộng.", "source": "lesson.md", "locator": "line:1"}]

        result, traces = generate_lesson(records, "Tổng hợp", client)

        self.assertEqual("AI", result["scenes"][0]["title"])
        self.assertEqual(2, client.lesson_attempts)
        self.assertEqual(2, len(traces))
        repair_messages = [messages for messages, schema in client.calls if schema == "interactive_lesson_v2"][1]
        self.assertIn("scene 0 title must be non-empty text", repair_messages[-1]["content"])


if __name__ == "__main__":
    unittest.main()
