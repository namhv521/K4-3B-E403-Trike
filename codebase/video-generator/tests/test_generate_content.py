import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_content import generate_lesson
from test_lesson_schema import lesson


class FakeClient:
    def __init__(self, digest_text="ý chính"):
        self.calls = []
        self.digest_text = digest_text

    def chat_json(self, messages, schema):
        self.calls.append((messages, schema))
        if schema == "source_digest_v1":
            return {"facts": [self.digest_text], "source_refs": ["source"]}, {"schema": schema}
        return lesson(), {"schema": schema}


class ContentTests(unittest.TestCase):
    def test_multiple_source_batches_are_summarized_before_lesson(self):
        client = FakeClient()
        records = [
            {"text": "A" * 20, "source": "a.md", "locator": "line:1"},
            {"text": "B" * 20, "source": "b.md", "locator": "line:1"},
        ]
        _, traces = generate_lesson(records, "Tổng hợp", client, batch_chars=20)
        self.assertEqual(["source_digest_v1", "source_digest_v1", "interactive_lesson_v2"], [call[1] for call in client.calls])
        self.assertEqual(3, len(traces))

    def test_digest_reduction_keeps_final_request_inside_budget(self):
        client = FakeClient(digest_text="x" * 30)
        records = [
            {"text": str(index) * 20, "source": f"{index}.md", "locator": "line:1"}
            for index in range(8)
        ]
        generate_lesson(records, "Tổng hợp", client, batch_chars=20, digest_chars=220)
        final_messages = next(messages for messages, schema in client.calls if schema == "interactive_lesson_v2")
        final_payload = final_messages[1]["content"].split("SOURCE_DIGESTS:\n", 1)[1]
        self.assertLessEqual(len(final_payload), 220)


if __name__ == "__main__":
    unittest.main()
