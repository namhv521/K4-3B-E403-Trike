import assert from "node:assert/strict";
import test from "node:test";
import { LearningSession, allowlistedEvent, validateLesson } from "../core.mjs";

function lesson() {
  const options = [
    { id: "A", text: "Đúng", is_correct: true, misconception: null },
    { id: "B", text: "Sai B", is_correct: false, misconception: { id: "scope", label: "Nhầm phạm vi" } },
    { id: "C", text: "Sai C", is_correct: false, misconception: { id: "example", label: "Nhầm ví dụ" } },
    { id: "D", text: "Sai D", is_correct: false, misconception: { id: "term", label: "Nhầm thuật ngữ" } },
  ];
  return {
    title: "Ôn AI", narration: "Nội dung ôn tập.", duration_seconds: 60,
    scenes: [{ start: 0, end: 60, title: "AI", body: "Khái niệm", source_refs: ["src-1"] }],
    checkpoints: [{ id: "cp1", time: 20, concept: "AI", question: "AI là gì?", explanation: "AI là lĩnh vực rộng.", source_refs: ["src-1"], options }],
  };
}

test("manifest validates a grounded continuous lesson", () => {
  assert.equal(validateLesson(lesson(), new Set(["src-1"])).checkpoints[0].id, "cp1");
});

test("manifest rejects ungrounded citation and scene gap", () => {
  assert.throws(() => validateLesson(lesson(), new Set(["src-other"])), /catalog/);
  assert.throws(() => validateLesson(lesson(), new Set()), /catalog/);
  const data = lesson();
  data.scenes = [{ ...data.scenes[0], start: 1 }];
  assert.throws(() => validateLesson(data), /liên tục/);
});

test("session pauses at due checkpoint and keeps incorrect learner in control", () => {
  let now = 1_000;
  const session = new LearningSession(validateLesson(lesson()), { sessionId: "s1", now: () => now });
  assert.equal(session.openDueCheckpoint(19.99), null);
  assert.equal(session.openDueCheckpoint(20.01).id, "cp1");
  now += 1_700;
  const result = session.submitAnswer("B");
  assert.equal(result.kind, "incorrect");
  assert.equal(result.attempt.response_time_ms, 1700);
  assert.throws(() => session.resolveFeedback("edit"), /5 giây/);
  now += 5_000;
  const edit = session.resolveFeedback("edit");
  assert.equal(edit.time, 20);
  const retry = session.submitAnswer("A");
  assert.equal(retry.kind, "correct");
  const review = session.resolveFeedback("review");
  assert.equal(review.time, 15);
  assert.equal(session.score(), 0);
});

test("telemetry removes secrets and free-text fields", () => {
  const event = allowlistedEvent({
    session_id: "s1", timestamp: "2026-09-18T00:00:00Z", event: "video_seek",
    input_type: "mouse", input_value: "timeline", seek_from: 12.5, seek_to: 30,
    api_key: "secret", source_text: "private",
  });
  assert.deepEqual(event, {
    session_id: "s1", timestamp: "2026-09-18T00:00:00Z", event: "video_seek",
    input_type: "mouse", input_value: "timeline", seek_from: 12.5, seek_to: 30,
  });
});

test("a learner may delete local session telemetry", () => {
  const session = new LearningSession(validateLesson(lesson()), { sessionId: "s1", now: () => 0 });
  session.event("video_started");
  session.clearEvents();
  assert.equal(session.events.length, 0);
});

test("session summary reports end-of-video learning metrics", () => {
  let now = 1_000;
  const session = new LearningSession(validateLesson(lesson()), { sessionId: "s1", now: () => now });
  session.openDueCheckpoint(20);
  now += 2_000;
  session.submitAnswer("B");
  now += 5_000;
  session.resolveFeedback("edit");
  now += 1_000;
  session.submitAnswer("A");

  assert.deepEqual(session.summary(), {
    score: 0,
    first_attempt_correct: 0,
    first_attempt_accuracy: 0,
    answered_checkpoints: 1,
    total_checkpoints: 1,
    total_attempts: 2,
    average_response_time_ms: 1500,
  });
});

test("completion metrics flag a learner who finishes below half of video duration", () => {
  const session = new LearningSession(validateLesson(lesson()), { sessionId: "s1" });

  assert.deepEqual(session.completion(29), {
    completion_seconds: 29,
    duration_seconds: 60,
    watched_ratio: 48,
    needs_review: true,
  });
  assert.deepEqual(session.completion(30), {
    completion_seconds: 30,
    duration_seconds: 60,
    watched_ratio: 50,
    needs_review: false,
  });
});
