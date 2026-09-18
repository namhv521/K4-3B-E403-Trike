"""Deterministic learning state for the fullscreen recap player."""

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone


class Session:
    def __init__(self, lesson, session_id, started_at):
        self.lesson = deepcopy(lesson)
        self.session_id = session_id
        self.started_at = started_at
        self.active_checkpoint_id = None
        self.checkpoint_opened_at = None
        self.feedback_until = None
        self.attempts = {}
        self.first_attempt_results = {}
        self.completed = set()
        self.unlocked_through = self.lesson["checkpoints"][0]["time"]
        self.next_action = None
        self.events = []

    def _checkpoint(self, checkpoint_id):
        for checkpoint in self.lesson["checkpoints"]:
            if checkpoint["id"] == checkpoint_id:
                return checkpoint
        raise ValueError(f"Unknown checkpoint: {checkpoint_id}")

    def _event(self, event_type, now, **extra):
        item = {
            "session_id": self.session_id,
            "timestamp": datetime.fromtimestamp(now, timezone.utc).isoformat(),
            "event": event_type,
            **extra,
        }
        self.events.append(item)
        return item

    def open_checkpoint(self, checkpoint_id, now):
        checkpoint = self._checkpoint(checkpoint_id)
        self.active_checkpoint_id = checkpoint_id
        self.checkpoint_opened_at = now
        self.feedback_until = None
        self.next_action = None
        return self._event("checkpoint_opened", now, checkpoint_id=checkpoint_id, video_time=checkpoint["time"])

    def submit_answer(self, answer_id, now):
        if not self.active_checkpoint_id:
            raise ValueError("No checkpoint is open")
        checkpoint = self._checkpoint(self.active_checkpoint_id)
        option = next((item for item in checkpoint["options"] if item["id"].upper() == answer_id.upper()), None)
        if option is None:
            raise ValueError("Answer must be A, B, C or D")
        attempts = self.attempts.setdefault(checkpoint["id"], [])
        misconception = option.get("misconception") or {}
        attempt = {
            "attempt_number": len(attempts) + 1,
            "selected_answer": answer_id.upper(),
            "is_correct": option.get("is_correct") is True,
            "misconception_id": misconception.get("id"),
            "misconception_label": misconception.get("label"),
            "response_time_ms": round(max(0, now - self.checkpoint_opened_at) * 1000),
        }
        attempts.append(attempt)
        self.first_attempt_results.setdefault(checkpoint["id"], attempt["is_correct"])
        self._event(
            "answer_submitted", now, checkpoint_id=checkpoint["id"],
            video_time=checkpoint["time"], score=self.summary()["score"], **attempt,
        )
        if attempt["is_correct"]:
            self.completed.add(checkpoint["id"])
            index = self.lesson["checkpoints"].index(checkpoint)
            target = min(self.lesson["duration_seconds"], checkpoint["time"] + 10)
            unlocked = self.lesson["checkpoints"][index + 1]["time"] if index + 1 < len(self.lesson["checkpoints"]) else self.lesson["duration_seconds"]
            self.unlocked_through = max(self.unlocked_through, unlocked)
            self.feedback_until = None
            self.next_action = {"type": "seek", "time": target, "autoplay": True}
        else:
            self.feedback_until = now + 5
        return attempt

    def choose_recovery(self, command, now):
        if command not in {"0", "1"}:
            raise ValueError("Command must be 0 or 1")
        if not self.active_checkpoint_id or self.feedback_until is None:
            raise ValueError("No failed checkpoint is awaiting recovery")
        if now < self.feedback_until:
            raise ValueError("Wait for the 5 seconds explanation")
        checkpoint = self._checkpoint(self.active_checkpoint_id)
        target = 0
        if command == "0":
            self.completed.clear()
            self.unlocked_through = self.lesson["checkpoints"][0]["time"]
        else:
            self.completed.add(checkpoint["id"])
            index = self.lesson["checkpoints"].index(checkpoint)
            target = self.lesson["checkpoints"][index + 1]["time"] if index + 1 < len(self.lesson["checkpoints"]) else self.lesson["duration_seconds"]
            self.unlocked_through = max(self.unlocked_through, target)
        self._event(
            "recovery_selected", now, checkpoint_id=checkpoint["id"],
            video_time=checkpoint["time"], action_after_feedback="restart" if command == "0" else "skip",
        )
        self.active_checkpoint_id = None
        self.checkpoint_opened_at = None
        self.feedback_until = None
        self.next_action = {"type": "seek", "time": target, "autoplay": True}

    def due_checkpoint(self, video_time):
        return next((
            checkpoint for checkpoint in self.lesson["checkpoints"]
            if checkpoint["id"] not in self.completed
            and checkpoint["time"] <= video_time
            and checkpoint["time"] <= self.unlocked_through
        ), None)

    def summary(self):
        total = len(self.lesson["checkpoints"])
        correct = sum(value is True for value in self.first_attempt_results.values())
        mistakes = Counter(
            attempt["misconception_label"] or attempt["misconception_id"]
            for attempts in self.attempts.values() for attempt in attempts
            if attempt["misconception_id"]
        )
        corrected = sum(
            self.first_attempt_results.get(checkpoint_id) is False and any(item["is_correct"] for item in attempts[1:])
            for checkpoint_id, attempts in self.attempts.items()
        )
        return {
            "score": round(correct / total * 10, 1) if total else 0.0,
            "total_attempts": sum(len(items) for items in self.attempts.values()),
            "corrected_after_review": corrected,
            "misconception_counts": dict(mistakes),
        }
