"""Generate the structured recap lesson from traceable source records."""

import json
from hashlib import sha256
from pathlib import Path

from lesson_schema import validate_lesson


SYSTEM_PROMPT = """Bạn là agent biên tập video ôn tập. Chỉ dùng SOURCE_DIGESTS được cung cấp.
Trả về duy nhất JSON gồm version, title, duration_seconds, narration, scenes và checkpoints.
Ưu tiên độ bao phủ: chọn các khái niệm quan trọng từ mọi nhóm nguồn, không chỉ nguồn đầu tiên.
Lời đọc khoảng 180-230 từ tiếng Việt, chia tối thiểu 4 cảnh và có 3 checkpoint.
Mỗi cảnh và checkpoint phải có source_refs không rỗng, chỉ dùng mã trong ALLOWED_SOURCE_REFS.
Mỗi checkpoint có id, time, concept, question, explanation, source_refs và đúng 4 options A-D.
Mỗi option có id, text, is_correct; option sai phải có misconception {id,label}, option đúng có misconception null.
Có đúng một đáp án đúng. Các checkpoint cách nhau trên 10 giây. Nội dung mục tiêu dài 60-90 giây."""

LESSON_REPAIR_PROMPT = """JSON lesson vừa trả về không đạt schema bắt buộc: {error}.
Hãy trả về lại TOÀN BỘ JSON lesson đã sửa, không markdown và không giải thích. Giữ nội dung bám SOURCE_DIGESTS,
giữ source_refs chỉ trong ALLOWED_SOURCE_REFS, và điền mọi field bắt buộc cho scene/checkpoint/option."""

DIGEST_PROMPT = """Tóm tắt nhóm SOURCE_RECORDS thành JSON gồm facts và source_refs.
Giữ đủ các khái niệm, quan hệ, ví dụ và điểm dễ nhầm. Không thêm kiến thức ngoài nguồn."""


def _json_size(value):
    return len(json.dumps(value, ensure_ascii=False))


def source_catalog(records):
    """Return stable, text-free citations safe to publish with a lesson bundle."""
    catalog = []
    seen = set()
    for record in records:
        source = str(record.get("source", ""))
        locator = str(record.get("locator", ""))
        if not source or not locator:
            raise ValueError("Each source record requires source and locator")
        ref = "src-" + sha256(f"{source}\0{locator}".encode("utf-8")).hexdigest()[:12]
        if ref not in seen:
            catalog.append({"ref": ref, "source": Path(source).name, "locator": locator})
            seen.add(ref)
    if not catalog:
        raise ValueError("At least one source record is required")
    return catalog


def _attach_source_refs(records, catalog):
    refs_by_location = {
        (str(item["source"]), str(item["locator"])): item["ref"]
        for item in catalog
    }
    enriched = []
    for record in records:
        key = (Path(str(record.get("source", ""))).name, str(record.get("locator", "")))
        ref = refs_by_location.get(key)
        if ref is None:
            raise ValueError("Every source record must map to a published source reference")
        enriched.append({**record, "source_ref": ref})
    return enriched


def _digest_records(records):
    """Keep model input compact while retaining the published citation identifier."""
    return [
        {"text": record["text"], "source_ref": record["source_ref"]}
        for record in records
    ]


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


def _generate_valid_lesson(client, messages, allowed_source_refs):
    """Ask the model to repair a parseable but schema-invalid lesson before failing the job."""
    for attempt in range(3):
        lesson, trace = client.chat_json(messages, "interactive_lesson_v2")
        try:
            return validate_lesson(lesson, allowed_source_refs=allowed_source_refs), trace
        except ValueError as error:
            if attempt == 2:
                raise ValueError(f"Model returned an invalid interactive lesson after 3 attempts: {error}") from error
            messages = [
                *messages,
                {"role": "assistant", "content": json.dumps(lesson, ensure_ascii=False)},
                {"role": "user", "content": LESSON_REPAIR_PROMPT.format(error=str(error))},
            ]


def generate_lesson(records, prompt, client, batch_chars=12000, digest_chars=12000):
    digests, traces = [], []
    catalog = source_catalog(records)
    records = _digest_records(_attach_source_refs(records, catalog))
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
    allowed_source_refs = [item["ref"] for item in catalog]
    lesson_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Yêu cầu: {prompt}\nALLOWED_SOURCE_REFS:\n"
            f"{json.dumps(allowed_source_refs, ensure_ascii=False)}\nSOURCE_DIGESTS:\n{payload}"
        )},
    ]
    lesson, trace = _generate_valid_lesson(client, lesson_messages, allowed_source_refs)
    traces.append(trace)
    return lesson, traces
