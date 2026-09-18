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
  const event = allowlistedEvent({ session_id: "s1", timestamp: "2026-09-18T00:00:00Z", event: "answer_submitted", selected_answer: "B", api_key: "secret", source_text: "private" });
  assert.deepEqual(event, { session_id: "s1", timestamp: "2026-09-18T00:00:00Z", event: "answer_submitted", selected_answer: "B" });
});

test("a learner may delete local session telemetry", () => {
  const session = new LearningSession(validateLesson(lesson()), { sessionId: "s1", now: () => 0 });
  session.event("video_started");
  session.clearEvents();
  assert.equal(session.events.length, 0);
});
