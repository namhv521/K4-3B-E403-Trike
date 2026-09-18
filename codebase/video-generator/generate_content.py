"""Generate the structured recap lesson from traceable source records."""

import json

from lesson_schema import validate_lesson


SYSTEM_PROMPT = """Bạn là agent biên tập video ôn tập. Chỉ dùng SOURCE_DIGESTS được cung cấp.
Trả về duy nhất JSON gồm version, title, duration_seconds, narration, scenes và checkpoints.
Ưu tiên độ bao phủ: chọn các khái niệm quan trọng từ mọi nhóm nguồn, không chỉ nguồn đầu tiên.
Lời đọc khoảng 180-230 từ tiếng Việt, chia tối thiểu 4 cảnh và có 3 checkpoint.
Mỗi checkpoint có id, time, concept, question, explanation, source_refs và đúng 4 options A-D.
Mỗi option có id, text, is_correct; option sai phải có misconception {id,label}, option đúng có misconception null.
Có đúng một đáp án đúng. Các checkpoint cách nhau trên 10 giây. Nội dung mục tiêu dài 60-90 giây."""

DIGEST_PROMPT = """Tóm tắt nhóm SOURCE_RECORDS thành JSON gồm facts và source_refs.
Giữ đủ các khái niệm, quan hệ, ví dụ và điểm dễ nhầm. Không thêm kiến thức ngoài nguồn."""


def _json_size(value):
    return len(json.dumps(value, ensure_ascii=False))


def _split_record(record, limit):
    if _json_size([record]) <= limit:
        return [record]
    if not isinstance(record.get("text"), str) or not record["text"]:
        raise ValueError("A source record exceeds the digest context budget")

    chunks, remaining, number = [], record["text"], 1
    locator = record.get("locator", record.get("source", "source"))
    while remaining:
        low, high, best = 1, len(remaining), None
        while low <= high:
            length = (low + high) // 2
            candidate = {
                **record,
                "text": remaining[:length],
                "locator": f"{locator}:chunk:{number}",
            }
            if _json_size([candidate]) <= limit:
                best, low = candidate, length + 1
            else:
                high = length - 1
        if best is None:
            raise ValueError("Digest context budget is too small for source metadata")
        chunks.append(best)
        remaining = remaining[len(best["text"]):]
        number += 1
    return chunks


def _batch_records(records, limit):
    batches, current = [], []
    expanded = [part for record in records for part in _split_record(record, limit)]
    for record in expanded:
        if current and _json_size(current + [record]) > limit:
            batches.append(current)
            current = []
        if _json_size([record]) > limit:
            raise ValueError("A source record exceeds the digest context budget")
        current.append(record)
    if current:
        batches.append(current)
    return batches


def _digest_batch(batch, client):
    return client.chat_json([
        {"role": "system", "content": DIGEST_PROMPT},
        {"role": "user", "content": json.dumps(batch, ensure_ascii=False)},
    ], "source_digest_v1")


def generate_lesson(records, prompt, client, batch_chars=12000, digest_chars=12000):
    digests, traces = [], []
    for batch in _batch_records(records, batch_chars):
        digest, trace = _digest_batch(batch, client)
        digests.append(digest)
        traces.append(trace)
    for _ in range(8):
        if len(json.dumps(digests, ensure_ascii=False)) <= digest_chars:
            break
        reduced = []
        for batch in _batch_records(digests, digest_chars):
            digest, trace = _digest_batch(batch, client)
            reduced.append(digest)
            traces.append(trace)
        digests = reduced
    else:
        raise ValueError("Source digests could not be reduced to the final context budget")
    payload = json.dumps(digests, ensure_ascii=False)
    lesson, trace = client.chat_json([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Yêu cầu: {prompt}\nSOURCE_DIGESTS:\n{payload}"},
    ], "interactive_lesson_v2")
    traces.append(trace)
    return validate_lesson(lesson), traces
