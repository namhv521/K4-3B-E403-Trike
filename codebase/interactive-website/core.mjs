export const ALLOWED_EVENT_FIELDS = new Set([
  "session_id", "timestamp", "event", "video_time", "checkpoint_id",
  "attempt_number", "selected_answer", "is_correct", "misconception_id",
  "misconception_label", "action_after_feedback", "response_time_ms", "score",
  "input_type", "input_value", "seek_from", "seek_to",
]);

const EPSILON = 0.001;

function requireText(value, field) {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${field} phải là chuỗi không rỗng.`);
  }
  return value.trim();
}

function requireSourceRefs(value, field, allowedSourceRefs) {
  if (!Array.isArray(value) || value.length === 0) {
    throw new Error(`${field} phải có ít nhất một nguồn.`);
  }
  const refs = value.map((item) => requireText(item, `${field} item`));
  if (new Set(refs).size !== refs.length) {
    throw new Error(`${field} không được lặp nguồn.`);
  }
  if (allowedSourceRefs && refs.some((ref) => !allowedSourceRefs.has(ref))) {
    throw new Error(`${field} chứa nguồn không có trong catalog.`);
  }
  return refs;
}

export function validateLesson(data, allowedSourceRefs = null) {
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("lesson.json phải là một object.");
  }
  const lesson = structuredClone(data);
  lesson.title = requireText(lesson.title, "title");
  lesson.narration = requireText(lesson.narration, "narration");
  if (!Number.isFinite(lesson.duration_seconds) || lesson.duration_seconds <= 0) {
    throw new Error("duration_seconds phải dương.");
  }
  if (!Array.isArray(lesson.scenes) || lesson.scenes.length === 0) {
    throw new Error("scenes không được rỗng.");
  }
  let previousEnd = 0;
  lesson.scenes.forEach((scene, index) => {
    if (!Number.isFinite(scene.start) || !Number.isFinite(scene.end) || scene.start < 0 || scene.end <= scene.start || scene.end > lesson.duration_seconds) {
      throw new Error(`Mốc thời gian cảnh ${index + 1} không hợp lệ.`);
    }
    if (Math.abs(scene.start - previousEnd) > EPSILON) {
      throw new Error("Các cảnh phải tạo thành timeline liên tục.");
    }
    scene.title = requireText(scene.title, `scene ${index + 1} title`);
    scene.body = requireText(scene.body, `scene ${index + 1} body`);
    scene.source_refs = requireSourceRefs(scene.source_refs, `scene ${index + 1} source_refs`, allowedSourceRefs);
    previousEnd = scene.end;
  });
  if (Math.abs(previousEnd - lesson.duration_seconds) > EPSILON) {
    throw new Error("Cảnh cuối phải kết thúc tại duration_seconds.");
  }
  if (!Array.isArray(lesson.checkpoints) || lesson.checkpoints.length === 0) {
    throw new Error("checkpoints không được rỗng.");
  }
  const ids = new Set();
  let previousTime = -11;
  lesson.checkpoints.forEach((checkpoint, index) => {
    checkpoint.id = requireText(checkpoint.id, `checkpoint ${index + 1} id`);
    if (ids.has(checkpoint.id)) throw new Error("Checkpoint id phải duy nhất.");
    ids.add(checkpoint.id);
    if (!Number.isFinite(checkpoint.time) || checkpoint.time <= 0 || checkpoint.time >= lesson.duration_seconds || checkpoint.time - previousTime <= 10) {
      throw new Error("Checkpoint phải nằm trong video và cách nhau hơn 10 giây.");
    }
    previousTime = checkpoint.time;
    ["concept", "question", "explanation"].forEach((field) => {
      checkpoint[field] = requireText(checkpoint[field], `checkpoint ${checkpoint.id} ${field}`);
    });
    checkpoint.source_refs = requireSourceRefs(checkpoint.source_refs, `checkpoint ${checkpoint.id} source_refs`, allowedSourceRefs);
    if (!Array.isArray(checkpoint.options) || checkpoint.options.length !== 4) {
      throw new Error("Mỗi checkpoint phải có đúng bốn phương án.");
    }
    const optionIds = new Set();
    let correct = 0;
    checkpoint.options.forEach((option) => {
      option.id = requireText(option.id, "option id").toUpperCase();
      option.text = requireText(option.text, "option text");
      optionIds.add(option.id);
      if (option.is_correct === true) correct += 1;
      if (option.is_correct !== true && (!option.misconception || !requireText(option.misconception.id, "misconception id") || !requireText(option.misconception.label, "misconception label"))) {
        throw new Error("Mỗi phương án sai cần misconception.");
      }
    });
    if (correct !== 1 || optionIds.size !== 4 || !["A", "B", "C", "D"].every((id) => optionIds.has(id))) {
      throw new Error("Phương án phải là A–D và có đúng một đáp án đúng.");
    }
  });
  return lesson;
}

export function allowlistedEvent(event) {
  const result = {};
  for (const [key, value] of Object.entries(event)) {
    if (ALLOWED_EVENT_FIELDS.has(key)) result[key] = value;
  }
  for (const field of ["session_id", "timestamp", "event"]) {
    if (typeof result[field] !== "string" || !result[field].trim()) {
      throw new Error(`${field} là bắt buộc cho telemetry.`);
    }
  }
  return result;
}

export class LearningSession {
  constructor(lesson, { sessionId = "session", now = () => Date.now() } = {}) {
    this.lesson = lesson;
    this.sessionId = sessionId;
    this.now = now;
    this.completed = new Set();
    this.attempts = new Map();
    this.firstAttemptResults = new Map();
    this.activeCheckpointId = null;
    this.openedAt = null;
    this.feedbackAvailableAt = null;
    this.events = [];
  }

  checkpoint(id) {
    const checkpoint = this.lesson.checkpoints.find((item) => item.id === id);
    if (!checkpoint) throw new Error(`Không tìm thấy checkpoint ${id}.`);
    return checkpoint;
  }

  score() {
    const correct = [...this.firstAttemptResults.values()].filter(Boolean).length;
    return Math.round((correct / this.lesson.checkpoints.length) * 100) / 10;
  }

  event(type, details = {}) {
    const item = allowlistedEvent({
      session_id: this.sessionId,
      timestamp: new Date(this.now()).toISOString(),
      event: type,
      score: this.score(),
      ...details,
    });
    this.events.push(item);
    return item;
  }

  clearEvents() {
    this.events.length = 0;
  }

  dueCheckpoint(videoTime) {
    return this.lesson.checkpoints.find((item) => !this.completed.has(item.id) && item.time <= videoTime + EPSILON) || null;
  }

  openDueCheckpoint(videoTime) {
    if (this.activeCheckpointId) return null;
    const checkpoint = this.dueCheckpoint(videoTime);
    if (!checkpoint) return null;
    this.activeCheckpointId = checkpoint.id;
    this.openedAt = this.now();
    this.event("checkpoint_opened", { checkpoint_id: checkpoint.id, video_time: checkpoint.time });
    return checkpoint;
  }

  requestHint() {
    if (!this.activeCheckpointId) throw new Error("Không có checkpoint đang mở.");
    const checkpoint = this.checkpoint(this.activeCheckpointId);
    return {
      kind: "uncertain",
      checkpoint,
      event: this.event("hint_requested", { checkpoint_id: checkpoint.id, video_time: checkpoint.time }),
    };
  }

  submitAnswer(optionId) {
    if (!this.activeCheckpointId) throw new Error("Không có checkpoint đang mở.");
    const checkpoint = this.checkpoint(this.activeCheckpointId);
    const option = checkpoint.options.find((item) => item.id === String(optionId).toUpperCase());
    if (!option) throw new Error("Câu trả lời phải là A, B, C hoặc D.");
    const attempts = this.attempts.get(checkpoint.id) || [];
    const responseTime = Math.max(0, this.now() - this.openedAt);
    const attempt = {
      attempt_number: attempts.length + 1,
      selected_answer: option.id,
      is_correct: option.is_correct === true,
      misconception_id: option.misconception?.id ?? null,
      misconception_label: option.misconception?.label ?? null,
      response_time_ms: Math.round(responseTime),
    };
    attempts.push(attempt);
    this.attempts.set(checkpoint.id, attempts);
    if (!this.firstAttemptResults.has(checkpoint.id)) this.firstAttemptResults.set(checkpoint.id, attempt.is_correct);
    this.feedbackAvailableAt = attempt.is_correct ? this.now() : this.now() + 5_000;
    return {
      kind: attempt.is_correct ? "correct" : "incorrect",
      checkpoint,
      attempt,
      event: this.event("answer_submitted", { checkpoint_id: checkpoint.id, video_time: checkpoint.time, ...attempt }),
    };
  }

  resolveFeedback(action) {
    if (!this.activeCheckpointId) throw new Error("Không có checkpoint đang mở.");
    const checkpoint = this.checkpoint(this.activeCheckpointId);
    if (this.feedbackAvailableAt !== null && this.now() < this.feedbackAvailableAt) {
      throw new Error("Hãy đọc lời giải đủ 5 giây trước khi chọn hướng tiếp theo.");
    }
    const permitted = new Set(["continue", "review", "edit"]);
    if (!permitted.has(action)) throw new Error("Hành động phản hồi không hợp lệ.");
    const event = this.event("feedback_action", {
      checkpoint_id: checkpoint.id,
      video_time: checkpoint.time,
      action_after_feedback: action,
    });
    if (action === "edit") {
      this.feedbackAvailableAt = null;
      this.openedAt = this.now();
      return { action, time: checkpoint.time, event };
    }
    this.completed.add(checkpoint.id);
    this.activeCheckpointId = null;
    this.openedAt = null;
    this.feedbackAvailableAt = null;
    return {
      action,
      time: action === "review" ? Math.max(0, checkpoint.time - 5) : Math.min(this.lesson.duration_seconds, checkpoint.time + 10),
      event,
    };
  }
}
