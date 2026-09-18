import { LearningSession, validateLesson } from "./core.mjs";

const bundleId = new URLSearchParams(location.search).get("bundle");
const bundle = bundleId
  ? { lesson: `/api/bundles/${encodeURIComponent(bundleId)}/lesson.json`, sources: `/api/bundles/${encodeURIComponent(bundleId)}/sources.json`, video: `/api/bundles/${encodeURIComponent(bundleId)}/recap.mp4` }
  : { lesson: "./assets/lesson.json", sources: "./assets/sources.json", video: "./assets/recap.mp4" };
const telemetryKey = "vlearn-interactive-session-events";
const $ = (selector) => document.querySelector(selector);
let videoFrameHandle = null;
let mediaVerified = false;

function sessionId() {
  return globalThis.crypto?.randomUUID?.() || `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatTime(seconds) {
  const minute = Math.floor(seconds / 60);
  return `${minute}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;
}

function exportEvents(events) {
  const blob = new Blob([events.map((item) => JSON.stringify(item)).join("\n") + "\n"], { type: "application/x-ndjson" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "vlearn-interactive-session.jsonl";
  link.click();
  URL.revokeObjectURL(url);
}

async function getJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`Không thể tải ${url}.`);
  return response.json();
}

function renderSources(checkpoint, sources) {
  const list = $("#source-list");
  list.replaceChildren();
  checkpoint.source_refs.forEach((ref) => {
    const item = sources.get(ref);
    const line = document.createElement("li");
    line.textContent = item ? `${item.source} · ${item.locator}` : `Mã nguồn: ${ref}`;
    list.append(line);
  });
}

function formatElapsed(seconds) {
  const rounded = Math.max(0, Math.round(seconds));
  const minute = Math.floor(rounded / 60);
  const second = rounded % 60;
  return minute ? `${minute} phút ${second} giây` : `${second} giây`;
}

function eventMessage(event) {
  const labels = {
    keyboard_input: `Bấm phím ${event.input_value}`,
    pointer_input: `Nhấp chuột: ${event.input_value}`,
    video_play: `Phát video tại ${formatTime(event.video_time || 0)}`,
    video_pause: `Dừng video tại ${formatTime(event.video_time || 0)}`,
    video_seek: `Tua video ${formatTime(event.seek_from || 0)} → ${formatTime(event.seek_to || 0)}`,
    checkpoint_opened: `Mở checkpoint ${event.checkpoint_id}`,
    answer_submitted: `Chọn đáp án ${event.selected_answer}`,
    hint_requested: `Yêu cầu gợi ý tại ${event.checkpoint_id}`,
    feedback_action: `Chọn ${event.action_after_feedback}`,
    session_completed: `Hoàn thành video: ${event.score}/10 điểm`,
  };
  return labels[event.event] || event.event;
}

function initialise(lesson, sources) {
  const video = $("#lesson-video");
  const overlay = $("#checkpoint-overlay");
  const status = $("#learning-status");
  const question = $("#checkpoint-question");
  const options = $("#answer-options");
  const feedback = $("#feedback");
  const feedbackText = $("#feedback-text");
  const continueButton = $("#continue-button");
  const reviewButton = $("#review-button");
  const editButton = $("#edit-button");
  const hintButton = $("#hint-button");
  const sourceButton = $("#source-button");
  const sourcePanel = $("#source-panel");
  const logList = $("#log-list");
  const logEmpty = $("#log-empty");
  const logCount = $("#log-count");
  const resultOverlay = $("#result-overlay");
  const session = new LearningSession(lesson, { sessionId: sessionId() });
  let displayedCheckpoint = null;
  let feedbackTimer = null;
  let renderedEvents = 0;
  let sentEvents = 0;
  let previousVideoTime = 0;
  let programmaticSeekTarget = null;
  let recentInputType = "mouse";
  let resultShown = false;
  let startedAt = null;
  const background = document.querySelectorAll(".lesson-header, .lesson-intro, .learning-notes, .privacy-note, #lesson-video");

  document.title = `${lesson.title} · VLearn`;
  $("#lesson-title").textContent = lesson.title;
  $("#duration").textContent = formatTime(lesson.duration_seconds);
  const generationNotice = $("#generation-notice");
  if (lesson.generation?.mode === "mock") {
    generationNotice.textContent = "Bản demo mock: nội dung fixture, không gọi OpenRouter.";
    generationNotice.hidden = false;
  }
  video.src = bundle.video;

  const renderEvents = () => {
    while (renderedEvents < session.events.length) {
      const event = session.events[renderedEvents];
      const row = document.createElement("li");
      row.className = "log-entry";
      const time = document.createElement("time");
      time.className = "log-time";
      time.dateTime = event.timestamp;
      time.textContent = new Date(event.timestamp).toLocaleTimeString("vi-VN", { hour12: false });
      const message = document.createElement("span");
      message.className = "log-message";
      message.textContent = eventMessage(event);
      row.append(time, message);
      logList.prepend(row);
      renderedEvents += 1;
    }
    logEmpty.hidden = session.events.length > 0;
    logCount.textContent = `${session.events.length} sự kiện`;
  };
  const sendEvent = (event) => {
    if (!bundleId) return;
    const body = JSON.stringify({bundle_id: bundleId, ...event});
    if (navigator.sendBeacon?.("/api/events", new Blob([body], {type: "application/json"}))) return;
    fetch("/api/events", {method: "POST", headers: {"Content-Type": "application/json"}, body, keepalive: true}).catch(() => {});
  };
  const log = () => {
    sessionStorage.setItem(telemetryKey, JSON.stringify(session.events));
    while (sentEvents < session.events.length) sendEvent(session.events[sentEvents++]);
    renderEvents();
  };
  const record = (event, details = {}) => {
    session.event(event, details);
    log();
  };
  const seekTo = (time) => {
    programmaticSeekTarget = time;
    video.currentTime = time;
  };
  const setStatus = (text) => { status.textContent = text; };
  const hideOverlay = () => {
    if (feedbackTimer) clearTimeout(feedbackTimer);
    feedbackTimer = null;
    overlay.hidden = true;
    feedback.hidden = true;
    sourcePanel.hidden = true;
    sourceButton.setAttribute("aria-expanded", "false");
    displayedCheckpoint = null;
    background.forEach((element) => { element.inert = false; });
    video.focus();
  };

  const openCheckpoint = (checkpoint) => {
    displayedCheckpoint = checkpoint;
    video.pause();
    seekTo(checkpoint.time);
    question.textContent = checkpoint.question;
    options.replaceChildren();
    checkpoint.options.forEach((option) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "answer-option";
      button.dataset.option = option.id;
      const label = document.createElement("span");
      const text = document.createElement("strong");
      label.textContent = option.id;
      text.textContent = option.text;
      button.append(label, text);
      button.addEventListener("click", () => answer(option.id));
      options.append(button);
    });
    overlay.hidden = false;
    background.forEach((element) => { element.inert = true; });
    feedback.hidden = true;
    sourcePanel.hidden = true;
    setStatus(`Checkpoint: ${checkpoint.concept}. Video đang tạm dừng.`);
    options.querySelector("button")?.focus();
    log();
  };

  const answer = (optionId) => {
    const result = session.submitAnswer(optionId);
    log();
    options.querySelectorAll("button").forEach((button) => {
      const option = result.checkpoint.options.find((item) => item.id === button.dataset.option);
      const selected = button.dataset.option === result.attempt.selected_answer;
      button.disabled = true;
      button.classList.toggle("is-correct", option?.is_correct === true);
      button.classList.toggle("is-incorrect", selected && option?.is_correct !== true);
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-label", `${button.textContent}: ${option?.is_correct ? "đáp án đúng" : selected ? "đáp án đã chọn, chưa đúng" : "đáp án chưa đúng"}`);
    });
    feedback.hidden = false;
    feedback.dataset.kind = result.kind;
    continueButton.hidden = false;
    reviewButton.hidden = false;
    editButton.hidden = false;
    [continueButton, reviewButton, editButton].forEach((button) => { button.disabled = result.kind === "incorrect"; });
    if (result.kind === "correct") {
      feedbackText.textContent = `Bạn đã đối chiếu đúng: ${result.checkpoint.explanation}`;
      continueButton.textContent = "Tiếp tục từ đoạn kế";
      setStatus("Câu trả lời có căn cứ. Bạn có thể tiếp tục hoặc xem lại.");
    } else {
      feedbackText.textContent = `Điểm cần ôn: ${result.attempt.misconception_label}. ${result.checkpoint.explanation}`;
      continueButton.textContent = "Tiếp tục bài";
      setStatus("Câu trả lời cần ôn lại. Hãy đọc lời giải trong 5 giây.");
      feedbackTimer = setTimeout(() => {
        [continueButton, reviewButton, editButton].forEach((button) => { button.disabled = false; });
        setStatus("Bạn có thể xem lại, sửa đáp án hoặc tiếp tục bài.");
        reviewButton.focus();
        feedbackTimer = null;
      }, 5_000);
    }
  };

  const resolve = (action) => {
    const result = session.resolveFeedback(action);
    log();
    if (action === "edit") {
      feedback.hidden = true;
      options.querySelectorAll("button").forEach((button) => {
        button.disabled = false;
        button.classList.remove("is-correct", "is-incorrect", "is-selected");
        button.removeAttribute("aria-label");
      });
      setStatus("Bạn có thể chọn lại câu trả lời. Video vẫn giữ tại checkpoint.");
      return;
    }
    hideOverlay();
    seekTo(result.time);
    video.play().catch(() => setStatus("Chọn nút phát để tiếp tục video."));
    setStatus(action === "review" ? "Đang xem lại 5 giây trước checkpoint." : "Đang tiếp tục bài học.");
  };

  const checkTiming = () => {
    if (mediaVerified && !session.activeCheckpointId) {
      const checkpoint = session.openDueCheckpoint(video.currentTime);
      if (checkpoint) openCheckpoint(checkpoint);
    }
  };
  const scheduleFrameCheck = () => {
    if (videoFrameHandle === null && typeof video.requestVideoFrameCallback === "function") {
      videoFrameHandle = video.requestVideoFrameCallback(() => {
        videoFrameHandle = null;
        checkTiming();
        if (!video.paused) scheduleFrameCheck();
      });
    }
  };

  video.addEventListener("loadedmetadata", () => {
    if (Math.abs(video.duration - lesson.duration_seconds) > 1.5) {
      setStatus("Thời lượng media không khớp manifest. Không bắt đầu phiên học.");
      video.pause();
      return;
    }
    mediaVerified = true;
    setStatus("Sẵn sàng. Video chỉ dùng cho luyện tập; không phải bài chấm điểm.");
  });
  video.addEventListener("timeupdate", () => {
    checkTiming();
    if (!video.seeking) previousVideoTime = video.currentTime;
  });
  video.addEventListener("seeking", () => {
    checkTiming();
    if (programmaticSeekTarget !== null && Math.abs(video.currentTime - programmaticSeekTarget) < 0.25) {
      programmaticSeekTarget = null;
      return;
    }
    programmaticSeekTarget = null;
    record("video_seek", {
      input_type: recentInputType, input_value: "timeline",
      video_time: video.currentTime, seek_from: previousVideoTime, seek_to: video.currentTime,
    });
  });
  video.addEventListener("seeked", () => { previousVideoTime = video.currentTime; });
  video.addEventListener("play", () => {
    startedAt ??= Date.now();
    record("video_play", { input_type: "media", input_value: "play", video_time: video.currentTime });
    scheduleFrameCheck();
  });
  video.addEventListener("pause", () => {
    record("video_pause", { input_type: "media", input_value: "pause", video_time: video.currentTime });
    if (videoFrameHandle && typeof video.cancelVideoFrameCallback === "function") video.cancelVideoFrameCallback(videoFrameHandle);
    videoFrameHandle = null;
  });
  video.addEventListener("ended", () => {
    if (resultShown) return;
    resultShown = true;
    const summary = session.summary();
    const completion = session.completion(startedAt === null ? 0 : (Date.now() - startedAt) / 1000);
    record("session_completed", { ...summary, ...completion, video_time: video.duration });
    $("#result-score").textContent = `${summary.score}/10`;
    $("#result-accuracy").textContent = `${summary.first_attempt_accuracy}%`;
    $("#result-checkpoints").textContent = `${summary.answered_checkpoints}/${summary.total_checkpoints}`;
    $("#result-attempts").textContent = String(summary.total_attempts);
    $("#result-response-time").textContent = `${(summary.average_response_time_ms / 1000).toFixed(1)} giây`;
    $("#result-completion-time").textContent = `Thời gian hoàn thành: ${formatElapsed(completion.completion_seconds)} / video ${formatElapsed(completion.duration_seconds)} (${completion.watched_ratio}%)`;
    const assessment = $("#result-viewing-assessment");
    assessment.classList.toggle("needs-review", completion.needs_review);
    assessment.textContent = completion.needs_review
      ? "Cần xem lại: bạn hoàn thành quá nhanh, có khả năng đã tua nội dung. Hãy ôn lại các checkpoint và kỹ năng cần củng cố."
      : "Thời gian học phù hợp với thời lượng video.";
    resultOverlay.hidden = false;
    setStatus(`Đã hoàn thành video với ${summary.score}/10 điểm.`);
  });
  video.addEventListener("error", () => setStatus("Không phát được video. Kiểm tra bundle recap.mp4."));

  continueButton.addEventListener("click", () => resolve("continue"));
  reviewButton.addEventListener("click", () => resolve("review"));
  editButton.addEventListener("click", () => resolve("edit"));
  hintButton.addEventListener("click", () => {
    const result = session.requestHint();
    log();
    feedback.hidden = false;
    feedback.dataset.kind = "uncertain";
    feedbackText.textContent = `Gợi ý: hãy đối chiếu lại khái niệm “${result.checkpoint.concept}” trong nguồn trước khi chọn.`;
    setStatus("Chưa chắc không bị chấm sai. Bạn có thể xem nguồn hoặc tự xem lại.");
  });
  sourceButton.addEventListener("click", () => {
    if (!displayedCheckpoint) return;
    renderSources(displayedCheckpoint, sources);
    sourcePanel.hidden = !sourcePanel.hidden;
    sourceButton.setAttribute("aria-expanded", String(!sourcePanel.hidden));
  });
  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (event.repeat || event.ctrlKey || event.metaKey || event.altKey || target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target?.isContentEditable) return;
    const key = event.key === " " ? "Space" : event.key;
    recentInputType = "keyboard";
    if (!["Shift", "Control", "Alt", "Meta"].includes(key)) {
      record("keyboard_input", { input_type: "keyboard", input_value: key, video_time: video.currentTime });
    }
    const answerKey = key.toUpperCase();
    const answerButton = options.querySelector(`[data-option="${answerKey}"]`);
    if (session.activeCheckpointId && feedback.hidden && answerButton && !answerButton.disabled) {
      event.preventDefault();
      answer(answerKey);
    }
  });
  document.addEventListener("pointerdown", () => { recentInputType = "mouse"; }, true);
  document.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    const control = event.target.closest("button, a, video");
    if (!control) return;
    const value = control.dataset.option ? `answer:${control.dataset.option}` : control.id || control.tagName.toLowerCase();
    record("pointer_input", { input_type: "mouse", input_value: value, video_time: video.currentTime });
  }, true);
  $("#export-log").addEventListener("click", () => exportEvents(session.events));
  $("#clear-log").addEventListener("click", () => {
    session.clearEvents();
    sessionStorage.removeItem(telemetryKey);
    logList.replaceChildren();
    renderedEvents = 0;
    sentEvents = 0;
    renderEvents();
    setStatus("Đã xóa log lưu trong tab này.");
  });
}

async function boot() {
  const status = $("#learning-status");
  try {
    const [rawLesson, rawSources] = await Promise.all([getJson(bundle.lesson), getJson(bundle.sources)]);
    const refs = new Set((Array.isArray(rawSources) ? rawSources : []).map((item) => item.ref).filter(Boolean));
    const lesson = validateLesson(rawLesson, refs);
    const sources = new Map((Array.isArray(rawSources) ? rawSources : []).map((item) => [item.ref, item]));
    initialise(lesson, sources);
  } catch (error) {
    status.textContent = `Không thể mở bài học: ${error.message}`;
    console.error(error);
  }
}

boot();
