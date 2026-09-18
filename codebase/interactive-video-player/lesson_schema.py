"""Validate the generated lesson bundle before starting the GUI."""

from copy import deepcopy


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def _source_refs(value, field, allowed_source_refs):
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must contain at least one source reference")
    refs = [_text(item, f"{field} item") for item in value]
    if len(set(refs)) != len(refs):
        raise ValueError(f"{field} must not contain duplicate source references")
    if allowed_source_refs is not None:
        unsupported = set(refs) - set(allowed_source_refs)
        if unsupported:
            raise ValueError(f"{field} contains unsupported source references")
    return refs


def validate_lesson(data, allowed_source_refs=None):
    if not isinstance(data, dict):
        raise ValueError("lesson must be an object")
    lesson = deepcopy(data)
    lesson["title"] = _text(lesson.get("title"), "title")
    lesson["narration"] = _text(lesson.get("narration"), "narration")
    duration = lesson.get("duration_seconds")
    if not isinstance(duration, (int, float)) or duration <= 0:
        raise ValueError("duration_seconds must be positive")
    if not isinstance(lesson.get("scenes"), list) or not lesson["scenes"]:
        raise ValueError("scenes must not be empty")
    checkpoints = lesson.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        raise ValueError("checkpoints must not be empty")
    previous_end = 0.0
    for index, scene in enumerate(lesson["scenes"]):
        start, end = scene.get("start"), scene.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            raise ValueError(f"scene {index} timing must be numeric")
        if start < 0 or end <= start or end > duration:
            raise ValueError(f"scene {index} timing must be inside the video")
        if abs(start - previous_end) > 0.001:
            raise ValueError("scenes must form one continuous timeline")
        scene["start"] = float(start)
        scene["end"] = float(end)
        scene["title"] = _text(scene.get("title"), f"scene {index} title")
        scene["body"] = _text(scene.get("body"), f"scene {index} body")
        scene["source_refs"] = _source_refs(
            scene.get("source_refs"), f"scene {index} source_refs", allowed_source_refs
        )
        previous_end = float(end)
    if abs(previous_end - duration) > 0.001:
        raise ValueError("scenes must end at duration_seconds")

    previous_time, checkpoint_ids = -11.0, set()
    for index, checkpoint in enumerate(checkpoints):
        checkpoint_id = _text(checkpoint.get("id"), f"checkpoint {index} id")
        if checkpoint_id in checkpoint_ids:
            raise ValueError("checkpoint ids must be unique")
        checkpoint_ids.add(checkpoint_id)
        checkpoint["id"] = checkpoint_id
        checkpoint_time = checkpoint.get("time")
        if not isinstance(checkpoint_time, (int, float)) or not 0 < checkpoint_time < duration:
            raise ValueError("checkpoint time must be inside the video")
        if checkpoint_time - previous_time <= 10:
            raise ValueError("checkpoints must be more than 10 seconds apart")
        previous_time = checkpoint_time
        for field in ("concept", "question", "explanation"):
            checkpoint[field] = _text(checkpoint.get(field), f"checkpoint {checkpoint_id} {field}")
        checkpoint["source_refs"] = _source_refs(
            checkpoint.get("source_refs"), f"checkpoint {checkpoint_id} source_refs", allowed_source_refs
        )
        options = checkpoint.get("options")
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError("each checkpoint must have exactly four options")
        if sum(option.get("is_correct") is True for option in options) != 1:
            raise ValueError("each checkpoint must have exactly one correct option")
        option_ids = set()
        for option in options:
            option["id"] = _text(option.get("id"), "option id").upper()
            option["text"] = _text(option.get("text"), "option text")
            option_ids.add(option["id"])
            if option.get("is_correct") is not True:
                misconception = option.get("misconception")
                if not isinstance(misconception, dict):
                    raise ValueError("every wrong option requires a misconception")
                _text(misconception.get("id"), "misconception id")
                _text(misconception.get("label"), "misconception label")
        if option_ids != {"A", "B", "C", "D"}:
            raise ValueError("option ids must be A, B, C and D")
    return lesson
