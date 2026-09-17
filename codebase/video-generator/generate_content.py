"""Generate the structured recap lesson from traceable source records."""

import json

from lesson_schema import validate_lesson


SYSTEM_PROMPT = """Bạn là agent biên tập video ôn tập. Chỉ dùng SOURCE_RECORDS được cung cấp.
Trả về duy nhất JSON gồm version, title, duration_seconds, narration, scenes và checkpoints.
Mỗi checkpoint có id, time, concept, question, explanation, source_refs và đúng 4 options A-D.
Mỗi option có id, text, is_correct; option sai phải có misconception {id,label}, option đúng có misconception null.
Có đúng một đáp án đúng. Các checkpoint cách nhau trên 10 giây. Nội dung mục tiêu dài 60-90 giây."""


def generate_lesson(records, prompt, client):
    payload = json.dumps(records, ensure_ascii=False)
    lesson, trace = client.chat_json([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Yêu cầu: {prompt}\nSOURCE_RECORDS:\n{payload}"},
    ], "interactive_lesson_v1")
    return validate_lesson(lesson), [trace]
