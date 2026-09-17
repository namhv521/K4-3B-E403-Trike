const test = require('node:test');
const assert = require('node:assert/strict');
const { createSession, openCheckpoint, submitAnswer, chooseRecovery, summary } = require('../engine.js');

const lesson = {
  duration_seconds: 70,
  checkpoints: [
    {
      id: 'cp1', time: 20, concept: 'AI', explanation: 'AI là lĩnh vực rộng.',
      options: [
        { id: 'A', text: 'AI', is_correct: true, misconception: null },
        { id: 'B', text: 'ML', is_correct: false, misconception: { id: 'scope', label: 'Đảo phạm vi' } },
        { id: 'C', text: 'Email', is_correct: false, misconception: { id: 'example', label: 'Nhầm ví dụ' } },
        { id: 'D', text: 'Data', is_correct: false, misconception: { id: 'data', label: 'Nhầm dữ liệu' } }
      ]
    },
    {
      id: 'cp2', time: 45, concept: 'ML', explanation: 'ML nằm trong AI.',
      options: [
        { id: 'A', text: 'AI', is_correct: true, misconception: null },
        { id: 'B', text: 'Video', is_correct: false, misconception: { id: 'media', label: 'Nhầm phương tiện' } },
        { id: 'C', text: 'Ảnh', is_correct: false, misconception: { id: 'image', label: 'Nhầm dữ liệu' } },
        { id: 'D', text: 'Mạng', is_correct: false, misconception: { id: 'network', label: 'Nhầm hạ tầng' } }
      ]
    }
  ]
};

test('all first attempts correct produce 10 points', () => {
  let state = createSession(lesson, 's1', 0);
  state = openCheckpoint(state, 'cp1', 1000);
  state = submitAnswer(state, 'cp1', 'A', 2000);
  state = openCheckpoint(state, 'cp2', 3000);
  state = submitAnswer(state, 'cp2', 'A', 4000);
  assert.equal(summary(state).score, 10);
});

test('later correct answer is logged but does not restore first-attempt score', () => {
  let state = createSession(lesson, 's2', 0);
  state = openCheckpoint(state, 'cp1', 1000);
  state = submitAnswer(state, 'cp1', 'B', 2000);
  assert.equal(state.events.at(-1).misconception_id, 'scope');
  state = submitAnswer(state, 'cp1', 'A', 8000);
  assert.equal(state.attempts.cp1.length, 2);
  assert.equal(summary(state).score, 0);
  assert.equal(summary(state).correctedAfterReview, 1);
});

test('recovery command is blocked during five second explanation', () => {
  let state = createSession(lesson, 's3', 0);
  state = openCheckpoint(state, 'cp1', 1000);
  state = submitAnswer(state, 'cp1', 'B', 2000);
  assert.throws(() => chooseRecovery(state, '0', 6999), /5 seconds/);
});

test('command zero restarts and command one moves to next checkpoint', () => {
  let restart = createSession(lesson, 's4', 0);
  restart = openCheckpoint(restart, 'cp1', 1000);
  restart = submitAnswer(restart, 'cp1', 'B', 2000);
  restart = chooseRecovery(restart, '0', 7000);
  assert.equal(restart.nextAction.time, 0);

  let skip = createSession(lesson, 's5', 0);
  skip = openCheckpoint(skip, 'cp1', 1000);
  skip = submitAnswer(skip, 'cp1', 'B', 2000);
  skip = chooseRecovery(skip, '1', 7000);
  assert.equal(skip.nextAction.time, 45);
});

test('invalid recovery commands are rejected', () => {
  let state = createSession(lesson, 's6', 0);
  state = openCheckpoint(state, 'cp1', 1000);
  state = submitAnswer(state, 'cp1', 'B', 2000);
  assert.throws(() => chooseRecovery(state, '2', 7000), /0 or 1/);
});

test('correct answer at final checkpoint unlocks the end of the video', () => {
  let state = createSession(lesson, 's7', 0);
  state = openCheckpoint(state, 'cp2', 1000);
  state = submitAnswer(state, 'cp2', 'A', 2000);
  assert.equal(state.unlockedThrough, 70);
  assert.equal(state.nextAction.time, 55);
});

test('correct answer unlocks playback through the next checkpoint while seeking ten seconds', () => {
  let state = createSession(lesson, 's8', 0);
  state = openCheckpoint(state, 'cp1', 1000);
  state = submitAnswer(state, 'cp1', 'A', 2000);
  assert.equal(state.nextAction.time, 30);
  assert.equal(state.unlockedThrough, 45);
});
