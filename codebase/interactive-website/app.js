import { LearningSession, validateLesson } from "./core.mjs";

const bundle = { lesson: "./assets/lesson.json", sources: "./assets/sources.json", video: "./assets/recap.mp4" };
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
  const session = new LearningSession(lesson, { sessionId: sessionId() });
  let displayedCheckpoint = null;
  let feedbackTimer = null;
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

  const persist = () => sessionStorage.setItem(telemetryKey, JSON.stringify(session.events));
  const log = () => persist();
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
    video.currentTime = checkpoint.time;
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
    options.querySelectorAll("button").forEach((button) => { button.disabled = true; });
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
      options.querySelectorAll("button").forEach((button) => { button.disabled = false; });
      setStatus("Bạn có thể chọn lại câu trả lời. Video vẫn giữ tại checkpoint.");
      return;
    }
    hideOverlay();
    video.currentTime = result.time;
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
  video.addEventListener("timeupdate", checkTiming);
  video.addEventListener("seeking", checkTiming);
  video.addEventListener("play", scheduleFrameCheck);
  video.addEventListener("pause", () => {
    if (videoFrameHandle && typeof video.cancelVideoFrameCallback === "function") video.cancelVideoFrameCallback(videoFrameHandle);
    videoFrameHandle = null;
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
  $("#export-log").addEventListener("click", () => exportEvents(session.events));
  $("#clear-log").addEventListener("click", () => {
    session.clearEvents();
    sessionStorage.removeItem(telemetryKey);
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
