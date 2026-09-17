(() => {
  const video = document.querySelector('#lessonVideo');
  const layer = document.querySelector('#checkpointLayer');
  const sheet = document.querySelector('.checkpoint-sheet');
  const answerGrid = document.querySelector('#answerGrid');
  const feedback = document.querySelector('#feedbackPanel');
  const recoveryForm = document.querySelector('#recoveryForm');
  const recoveryInput = document.querySelector('#recoveryCommand');
  const commandError = document.querySelector('#commandError');
  let lesson;
  let state;
  let previousFocus;
  let countdownTimer;
  let internalSeek = false;
  let renderedEventCount = 0;

  const shell = document.querySelector('.shell');

  function trapFocus(event, container) {
    if (event.key !== 'Tab') return;
    const items = [...container.querySelectorAll('button:not(:disabled), input:not(:disabled), [tabindex]:not([tabindex="-1"])')]
      .filter(item => !item.hidden && item.offsetParent !== null);
    if (!items.length) return;
    const first = items[0];
    const last = items.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }

  const formatTime = seconds => {
    const value = Math.max(0, Math.floor(seconds || 0));
    return `${String(Math.floor(value / 60)).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}`;
  };

  const sessionKey = () => `recap-session:${lesson.version}:${lesson.title}`;
  const newSessionId = () => globalThis.crypto?.randomUUID?.() || `session-${Date.now()}`;

  function persist() {
    localStorage.setItem(sessionKey(), JSON.stringify(state));
  }

  async function sendEvent(event) {
    try {
      const response = await fetch('/api/logs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(event) });
      if (!response.ok) throw new Error('Log server rejected the event');
    } catch (error) {
      console.warn('Log retained in localStorage:', error.message);
    }
  }

  function flushNewEvents(before) {
    state.events.slice(before).forEach(sendEvent);
    persist();
    renderDashboard();
  }

  function recordUiEvent(type, extra = {}) {
    const event = { session_id: state.sessionId, timestamp: new Date().toISOString(), event: type, video_time: Number(video.currentTime.toFixed(2)), ...extra };
    state.events.push(event);
    sendEvent(event);
    persist();
    renderEvents();
  }

  function applyAction() {
    if (!state.nextAction) return;
    internalSeek = true;
    video.currentTime = state.nextAction.time;
    setTimeout(() => { internalSeek = false; }, 100);
    if (state.nextAction.autoplay) video.play().catch(() => {});
    state.nextAction = null;
    persist();
  }

  function openCheckpoint(checkpoint) {
    video.pause();
    const before = state.events.length;
    state = RecapEngine.openCheckpoint(state, checkpoint.id, Date.now());
    flushNewEvents(before);
    previousFocus = document.activeElement;
    document.querySelector('#checkpointMeta').textContent = `Checkpoint ${lesson.checkpoints.indexOf(checkpoint) + 1}/${lesson.checkpoints.length} · ${checkpoint.concept}`;
    document.querySelector('#questionText').textContent = checkpoint.question;
    document.querySelector('#countdown').textContent = '';
    feedback.hidden = true;
    feedback.className = 'feedback-panel';
    recoveryForm.hidden = true;
    commandError.textContent = '';
    answerGrid.innerHTML = '';
    checkpoint.options.forEach(option => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'answer-button';
      button.dataset.answer = option.id;
      const letter = document.createElement('span');
      letter.className = 'answer-letter';
      letter.textContent = option.id;
      const text = document.createElement('span');
      text.textContent = option.text;
      button.append(letter, text);
      button.addEventListener('click', () => answer(checkpoint, option.id));
      answerGrid.append(button);
    });
    layer.hidden = false;
    shell.inert = true;
    answerGrid.querySelector('button')?.focus();
  }

  function closeCheckpoint() {
    clearInterval(countdownTimer);
    layer.hidden = true;
    shell.inert = false;
    previousFocus?.focus();
  }

  layer.addEventListener('keydown', event => trapFocus(event, sheet));

  function answer(checkpoint, answerId) {
    const before = state.events.length;
    state = RecapEngine.submitAnswer(state, checkpoint.id, answerId, Date.now());
    flushNewEvents(before);
    const attempt = state.attempts[checkpoint.id].at(-1);
    answerGrid.querySelectorAll('button').forEach(button => {
      button.disabled = true;
      const option = checkpoint.options.find(item => item.id === button.dataset.answer);
      if (option.is_correct) button.classList.add('correct');
      if (button.dataset.answer === answerId && !attempt.is_correct) button.classList.add('wrong');
    });
    feedback.hidden = false;
    feedback.textContent = `${attempt.is_correct ? 'Chính xác.' : 'Chưa chính xác.'} ${checkpoint.explanation}`;
    if (attempt.is_correct) {
      feedback.classList.add('success');
      setTimeout(() => { closeCheckpoint(); applyAction(); }, 900);
      return;
    }
    startCountdown();
  }

  function startCountdown() {
    const countdown = document.querySelector('#countdown');
    const update = () => {
      const seconds = Math.max(0, Math.ceil((state.feedbackUntil - Date.now()) / 1000));
      countdown.textContent = seconds ? `${seconds}s` : '';
      if (!seconds) {
        clearInterval(countdownTimer);
        recoveryForm.hidden = false;
        recoveryInput.focus();
      }
    };
    update();
    countdownTimer = setInterval(update, 200);
  }

  recoveryForm.addEventListener('submit', event => {
    event.preventDefault();
    commandError.textContent = '';
    try {
      const before = state.events.length;
      state = RecapEngine.chooseRecovery(state, recoveryInput.value.trim(), Date.now());
      flushNewEvents(before);
      recoveryInput.value = '';
      closeCheckpoint();
      applyAction();
    } catch (error) {
      commandError.textContent = error.message === 'Command must be 0 or 1' ? 'Chỉ nhập 0 hoặc 1.' : 'Hãy chờ lời giải hiển thị đủ 5 giây.';
    }
  });

  function renderEvents() {
    const list = document.querySelector('#eventList');
    const names = { checkpoint_opened: 'Mở checkpoint', answer_submitted: 'Gửi đáp án', recovery_selected: 'Chọn hướng tiếp tục', video_played: 'Phát video', video_paused: 'Dừng video', seek_blocked: 'Chặn tua vượt nội dung', session_completed: 'Hoàn thành phiên' };
    if (renderedEventCount > state.events.length) {
      list.replaceChildren();
      renderedEventCount = 0;
    }
    state.events.slice(renderedEventCount).forEach(item => {
      const li = document.createElement('li');
      const strong = document.createElement('strong');
      strong.textContent = names[item.event] || item.event;
      const detail = document.createElement('span');
      detail.textContent = item.checkpoint_id ? `${item.checkpoint_id}${item.selected_answer ? ` · chọn ${item.selected_answer}` : ''}` : formatTime(item.video_time);
      li.append(strong, detail);
      list.append(li);
      while (list.children.length > 7) list.firstElementChild.remove();
    });
    renderedEventCount = state.events.length;
    list.scrollTop = list.scrollHeight;
  }

  function renderDashboard() {
    const report = RecapEngine.summary(state);
    document.querySelector('#scoreValue').textContent = `${report.score}/10`;
    document.querySelector('#progressValue').textContent = `${state.completed.length}/${lesson.checkpoints.length}`;
    document.querySelector('#attemptValue').textContent = report.totalAttempts;
    document.querySelector('#correctedValue').textContent = report.correctedAfterReview;
    document.querySelectorAll('.checkpoint-marker').forEach(marker => marker.classList.toggle('done', state.completed.includes(marker.dataset.id)));
    document.querySelectorAll('#conceptList li').forEach(item => item.classList.toggle('done', state.completed.includes(item.dataset.id)));
    renderEvents();
  }

  function renderLesson() {
    document.querySelector('#lessonTitle').textContent = lesson.title;
    document.querySelector('#lessonIntro').textContent = 'Trả lời để mở khóa từng phần; điểm chỉ tính ở lần chọn đầu tiên.';
    document.querySelector('#sessionLabel').textContent = state.sessionId.slice(0, 13);
    const badge = document.querySelector('#modeBadge');
    const isMock = lesson.generation?.mode === 'mock';
    badge.textContent = isMock ? 'Nội dung demo · mock' : 'OpenRouter · AI thật';
    badge.classList.toggle('mock', isMock);
    const markers = document.querySelector('#checkpointMarkers');
    const concepts = document.querySelector('#conceptList');
    lesson.checkpoints.forEach((checkpoint, index) => {
      const marker = document.createElement('span');
      marker.className = 'checkpoint-marker';
      marker.style.left = `${checkpoint.time / lesson.duration_seconds * 100}%`;
      marker.dataset.id = checkpoint.id;
      marker.dataset.label = `CP${index + 1}`;
      marker.title = `${checkpoint.concept} · ${formatTime(checkpoint.time)}`;
      marker.setAttribute('role', 'img');
      marker.setAttribute('aria-label', `Checkpoint ${index + 1}: ${checkpoint.concept}, tại ${formatTime(checkpoint.time)}`);
      markers.append(marker);
      const item = document.createElement('li');
      item.dataset.id = checkpoint.id;
      item.textContent = checkpoint.concept;
      concepts.append(item);
    });
    renderDashboard();
  }

  function updateProgress() {
    const duration = video.duration || lesson.duration_seconds;
    document.querySelector('#timeLabel').textContent = `${formatTime(video.currentTime)} / ${formatTime(duration)}`;
    document.querySelector('#progressFill').style.width = `${Math.min(100, video.currentTime / duration * 100)}%`;
    const next = lesson.checkpoints.find(item => !state.completed.includes(item.id) && item.time >= video.currentTime - .25);
    document.querySelector('#nextLabel').textContent = next ? `Tiếp theo: ${next.concept} · ${formatTime(next.time)}` : 'Không còn checkpoint';
  }

  video.addEventListener('timeupdate', () => {
    updateProgress();
    if (video.currentTime > state.unlockedThrough + .4) {
      internalSeek = true;
      video.currentTime = state.unlockedThrough;
      video.pause();
      setTimeout(() => { internalSeek = false; }, 100);
      document.querySelector('#lockedNotice').hidden = false;
      setTimeout(() => { document.querySelector('#lockedNotice').hidden = true; }, 1800);
      recordUiEvent('seek_blocked');
      return;
    }
    const checkpoint = lesson.checkpoints.find(item => !state.completed.includes(item.id) && video.currentTime >= item.time && video.currentTime < item.time + .7);
    if (checkpoint && layer.hidden) openCheckpoint(checkpoint);
  });

  video.addEventListener('seeking', () => {
    if (!internalSeek && video.currentTime > state.unlockedThrough) {
      video.currentTime = state.unlockedThrough;
      recordUiEvent('seek_blocked');
    }
  });
  video.addEventListener('play', () => recordUiEvent('video_played'));
  video.addEventListener('pause', () => { if (layer.hidden && !video.ended) recordUiEvent('video_paused'); });
  video.addEventListener('ended', finishSession);

  function finishSession() {
    const report = RecapEngine.summary(state);
    recordUiEvent('session_completed', { score: report.score });
    document.querySelector('#finalScore').textContent = `${report.score}/10`;
    const mistakes = Object.entries(report.misconceptionCounts).sort((a, b) => b[1] - a[1]);
    document.querySelector('#finalReport').innerHTML = '';
    const lines = [
      `Bạn đã thực hiện ${report.totalAttempts} lần trả lời.`,
      `Số checkpoint sửa đúng sau khi xem lại: ${report.correctedAfterReview}.`,
      mistakes.length ? `Nhầm lẫn nổi bật: ${mistakes.map(([name, count]) => `${name} (${count})`).join(', ')}.` : 'Không ghi nhận nhầm lẫn.'
    ];
    lines.forEach(text => { const p = document.createElement('p'); p.textContent = text; document.querySelector('#finalReport').append(p); });
    document.querySelector('#completionLayer').hidden = false;
    shell.inert = true;
    document.querySelector('#restartSession').focus();
  }

  document.querySelector('#completionLayer').addEventListener('keydown', event => trapFocus(event, document.querySelector('.completion-sheet')));

  document.querySelector('#restartSession').addEventListener('click', () => {
    localStorage.removeItem(sessionKey());
    location.reload();
  });

  async function init() {
    try {
      const response = await fetch('assets/lesson.json', { cache: 'no-store' });
      if (!response.ok) throw new Error('Không tải được lesson.json');
      lesson = await response.json();
      const saved = localStorage.getItem(sessionKey());
      state = saved ? JSON.parse(saved) : RecapEngine.createSession(lesson, newSessionId(), Date.now());
      renderLesson();
      updateProgress();
    } catch (error) {
      document.querySelector('#lessonTitle').textContent = 'Không thể mở bài học';
      document.querySelector('#lessonIntro').textContent = `${error.message}. Hãy chạy server.py và kiểm tra thư mục assets.`;
      video.hidden = true;
    }
  }

  init();
})();
