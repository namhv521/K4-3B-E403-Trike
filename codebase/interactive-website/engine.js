(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.RecapEngine = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const copy = value => JSON.parse(JSON.stringify(value));

  function createSession(lesson, sessionId, now = Date.now()) {
    return {
      lesson: copy(lesson), sessionId, startedAt: now, activeCheckpointId: null,
      checkpointOpenedAt: null, feedbackUntil: null, attempts: {}, firstAttemptResults: {},
      completed: [], unlockedThrough: lesson.checkpoints[0]?.time ?? lesson.duration_seconds,
      nextAction: null, events: []
    };
  }

  function event(state, type, now, extra = {}) {
    return {
      session_id: state.sessionId,
      timestamp: new Date(now).toISOString(),
      event: type,
      ...extra
    };
  }

  function findCheckpoint(state, id) {
    const checkpoint = state.lesson.checkpoints.find(item => item.id === id);
    if (!checkpoint) throw new Error(`Unknown checkpoint: ${id}`);
    return checkpoint;
  }

  function openCheckpoint(state, id, now = Date.now()) {
    const next = copy(state);
    const checkpoint = findCheckpoint(next, id);
    next.activeCheckpointId = id;
    next.checkpointOpenedAt = now;
    next.feedbackUntil = null;
    next.nextAction = null;
    next.events.push(event(next, 'checkpoint_opened', now, { checkpoint_id: id, video_time: checkpoint.time }));
    return next;
  }

  function submitAnswer(state, checkpointId, answerId, now = Date.now()) {
    const next = copy(state);
    const checkpoint = findCheckpoint(next, checkpointId);
    const option = checkpoint.options.find(item => item.id === answerId);
    if (!option) throw new Error('Answer must be A, B, C or D');
    const attempts = next.attempts[checkpointId] || [];
    const attemptNumber = attempts.length + 1;
    const responseTime = Math.max(0, now - (next.checkpointOpenedAt ?? now));
    const attempt = {
      attempt_number: attemptNumber,
      selected_answer: answerId,
      is_correct: option.is_correct === true,
      misconception_id: option.misconception?.id ?? null,
      misconception_label: option.misconception?.label ?? null,
      response_time_ms: responseTime
    };
    attempts.push(attempt);
    next.attempts[checkpointId] = attempts;
    if (!(checkpointId in next.firstAttemptResults)) next.firstAttemptResults[checkpointId] = attempt.is_correct;
    next.events.push(event(next, 'answer_submitted', now, {
      checkpoint_id: checkpointId, video_time: checkpoint.time, ...attempt,
      score: score(next)
    }));
    if (attempt.is_correct) {
      if (!next.completed.includes(checkpointId)) next.completed.push(checkpointId);
      const index = next.lesson.checkpoints.findIndex(item => item.id === checkpointId);
      const target = Math.min(next.lesson.duration_seconds, checkpoint.time + 10);
      const unlockedTarget = next.lesson.checkpoints[index + 1]?.time ?? next.lesson.duration_seconds;
      next.unlockedThrough = Math.max(next.unlockedThrough, unlockedTarget);
      next.feedbackUntil = null;
      next.nextAction = { type: 'seek', time: target, autoplay: true };
    } else {
      next.feedbackUntil = now + 5000;
      next.nextAction = null;
    }
    return next;
  }

  function chooseRecovery(state, command, now = Date.now()) {
    if (command !== '0' && command !== '1') throw new Error('Command must be 0 or 1');
    if (!state.activeCheckpointId || !state.feedbackUntil) throw new Error('No failed checkpoint is awaiting recovery');
    if (now < state.feedbackUntil) throw new Error('Wait for the 5 seconds explanation');
    const next = copy(state);
    const current = findCheckpoint(next, next.activeCheckpointId);
    let target = 0;
    if (command === '1') {
      if (!next.completed.includes(current.id)) next.completed.push(current.id);
      const index = next.lesson.checkpoints.findIndex(item => item.id === current.id);
      target = next.lesson.checkpoints[index + 1]?.time ?? next.lesson.duration_seconds;
      next.unlockedThrough = Math.max(next.unlockedThrough, target);
    }
    next.events.push(event(next, 'recovery_selected', now, {
      checkpoint_id: current.id,
      video_time: current.time,
      action_after_feedback: command === '0' ? 'restart' : 'skip'
    }));
    next.activeCheckpointId = null;
    next.checkpointOpenedAt = null;
    next.feedbackUntil = null;
    next.nextAction = { type: 'seek', time: target, autoplay: true };
    return next;
  }

  function score(state) {
    const total = state.lesson.checkpoints.length;
    const correct = Object.values(state.firstAttemptResults).filter(Boolean).length;
    return total ? Math.round(correct / total * 100) / 10 : 0;
  }

  function summary(state) {
    const misconceptionCounts = {};
    Object.values(state.attempts).flat().forEach(attempt => {
      if (attempt.misconception_id) {
        const key = attempt.misconception_label || attempt.misconception_id;
        misconceptionCounts[key] = (misconceptionCounts[key] || 0) + 1;
      }
    });
    const correctedAfterReview = Object.entries(state.attempts).filter(([id, attempts]) =>
      state.firstAttemptResults[id] === false && attempts.slice(1).some(item => item.is_correct)
    ).length;
    return {
      score: score(state),
      totalAttempts: Object.values(state.attempts).reduce((sum, items) => sum + items.length, 0),
      correctedAfterReview,
      misconceptionCounts
    };
  }

  return { createSession, openCheckpoint, submitAnswer, chooseRecovery, summary };
});
