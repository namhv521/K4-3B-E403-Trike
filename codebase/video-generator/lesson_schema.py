"""Small, dependency-free validator for generated lesson manifests."""

from copy import deepcopy


def checkpoint_score(correct_first_attempts: int, checkpoint_count: int) -> float:
    if checkpoint_count <= 0:
        return 0.0
    return round(correct_first_attempts / checkpoint_count * 10, 1)


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def validate_lesson(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("lesson must be an object")
    result = deepcopy(data)
    result["title"] = _text(result.get("title"), "title")
    result["narration"] = _text(result.get("narration"), "narration")
    duration = result.get("duration_seconds")
    if not isinstance(duration, (int, float)) or duration <= 0:
        raise ValueError("duration_seconds must be positive")
    scenes = result.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("scenes must not be empty")
    checkpoints = result.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        raise ValueError("checkpoints must not be empty")

    previous_time = -11.0
    seen_ids = set()
    for index, checkpoint in enumerate(checkpoints):
        checkpoint["id"] = _text(checkpoint.get("id"), f"checkpoint {index} id")
        if checkpoint["id"] in seen_ids:
            raise ValueError("checkpoint ids must be unique")
        seen_ids.add(checkpoint["id"])
        time = checkpoint.get("time")
        if not isinstance(time, (int, float)) or not 0 < time < duration:
            raise ValueError("checkpoint time must be inside the video")
        if time - previous_time <= 10:
            raise ValueError("checkpoints must be more than 10 seconds apart")
        previous_time = time
        for field in ("concept", "question", "explanation"):
            checkpoint[field] = _text(checkpoint.get(field), f"checkpoint {checkpoint['id']} {field}")
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
            if not option.get("is_correct"):
                misconception = option.get("misconception")
                if not isinstance(misconception, dict):
                    raise ValueError("every wrong option requires a misconception")
                _text(misconception.get("id"), "misconception id")
                _text(misconception.get("label"), "misconception label")
        if option_ids != {"A", "B", "C", "D"}:
            raise ValueError("option ids must be A, B, C and D")
    return result
