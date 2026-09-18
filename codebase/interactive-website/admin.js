import {filterSupportedFiles, unsupportedUploadMessage, validateAdminRequest} from "./admin-core.mjs";

const $ = (selector) => document.querySelector(selector);
const selectedBundleStorageKey = "vlearn-admin-selected-bundle";
let activeBundleId = null;
let pollTimer = null;

function renderRows(selector, rows, formatter, empty) {
  const list = $(selector);
  list.replaceChildren();
  if (!rows.length) {
    const item = document.createElement("li"); item.textContent = empty; list.append(item); return;
  }
  rows.forEach((row) => { const item = document.createElement("li"); item.textContent = formatter(row); list.append(item); });
}

async function loadAnalytics(bundleId) {
  const response = await fetch(`/api/admin/analytics?bundle_id=${encodeURIComponent(bundleId)}`);
  if (!response.ok) throw new Error("Không thể tải dashboard của lecture này.");
  const report = await response.json();
  $("#analytics-empty").hidden = true; $("#analytics").hidden = false;
  $("#metric-views").textContent = report.views;
  $("#metric-completed").textContent = report.completed_sessions;
  $("#metric-score").textContent = `${report.average_score.toFixed(1)}/10`;
  $("#metric-fast").textContent = report.fast_completion_count;
  $("#metric-response-time").textContent = `${(report.average_response_time_ms / 1000).toFixed(1)} giây`;
  $("#metric-completion-time").textContent = `${report.average_completion_seconds} giây`;
  renderRows("#checkpoint-analytics", report.checkpoints, (row) => `${row.checkpoint_id}: ${row.first_attempt_accuracy}% đúng lần đầu · ${row.incorrect} lượt sai`, "Chưa có câu trả lời.");
  renderRows("#misconception-analytics", report.misconceptions, (row) => `${row.label || row.misconception_id}: ${row.count} lần`, "Chưa ghi nhận nhầm lẫn.");
  renderRows("#session-analytics", report.sessions, (row) => {
    if (!row.completed) return `${row.session_id.slice(0, 8)}… · đang xem · ${row.event_count} event`;
    const score = typeof row.score === "number" ? `${row.score}/10 điểm` : "chưa có điểm";
    const accuracy = typeof row.first_attempt_accuracy === "number" ? ` · đúng lần đầu ${row.first_attempt_accuracy}%` : "";
    return `${row.session_id.slice(0, 8)}… · ${score}${accuracy} · đã hoàn thành`;
  }, "Chưa có phiên xem.");
  renderRows("#event-analytics", report.recent_events, (row) => {
    const checkpoint = row.checkpoint_id ? ` · ${row.checkpoint_id}` : "";
    const answer = typeof row.is_correct === "boolean" ? ` · ${row.is_correct ? "đúng" : "sai"}` : "";
    return `${new Date(row.timestamp).toLocaleTimeString("vi-VN", {hour12: false})} · ${row.session_id.slice(0, 8)}… · ${row.event}${checkpoint}${answer}`;
  }, "Chưa có hoạt động.");
}

function setActiveBundle(bundleId) {
  activeBundleId = bundleId || null;
  if (activeBundleId) localStorage.setItem(selectedBundleStorageKey, activeBundleId);
  else localStorage.removeItem(selectedBundleStorageKey);
}

async function loadPublishedLectures(preferredBundleId = null) {
  const response = await fetch("/api/admin/bundles", {cache: "no-store"});
  if (!response.ok) throw new Error("Không thể tải danh sách lecture.");
  const lectures = await response.json();
  const select = $("#lecture-select");
  select.replaceChildren();
  if (!lectures.length) {
    select.append(new Option("Chưa có lecture được publish", ""));
    select.disabled = true;
    setActiveBundle(null);
    $("#analytics").hidden = true;
    $("#analytics-empty").hidden = false;
    return;
  }
  lectures.forEach((lecture) => {
    select.append(new Option(`${lecture.title} · ${lecture.checkpoint_count} checkpoint`, lecture.bundle_id));
  });
  select.disabled = false;
  const available = new Set(lectures.map((lecture) => lecture.bundle_id));
  const chosen = [preferredBundleId, activeBundleId, localStorage.getItem(selectedBundleStorageKey), lectures[0].bundle_id]
    .find((bundleId) => available.has(bundleId));
  select.value = chosen;
  setActiveBundle(chosen);
  await loadAnalytics(chosen);
}

async function pollJob(jobId) {
  const response = await fetch(`/api/admin/jobs/${jobId}`, {cache: "no-store"});
  const job = await response.json();
  const status = $("#job-status");
  if (!response.ok) { status.textContent = job.error || "Không đọc được job."; return; }
  status.textContent = `Job ${job.status}${job.error ? `: ${job.error}` : ""}`;
  if (job.status === "succeeded") {
    clearInterval(pollTimer); pollTimer = null;
    const link = $("#bundle-link"); link.href = job.bundle_url; link.hidden = false;
    loadPublishedLectures(job.bundle_id).catch((error) => { status.textContent = error.message; }); return;
  }
  if (job.status === "failed") { clearInterval(pollTimer); pollTimer = null; }
}

$("#source-folder").addEventListener("change", (event) => {
  const {supported, ignored} = filterSupportedFiles([...event.target.files]);
  const ignoredNames = ignored.map((file) => file.webkitRelativePath || file.name).join(", ");
  $("#file-count").textContent = supported.length
    ? `${supported.length} file hợp lệ được chọn${ignored.length ? `; bỏ qua ${ignored.length} file không hỗ trợ: ${ignoredNames}. ${unsupportedUploadMessage(ignored)}` : ""}`
    : ignored.length ? unsupportedUploadMessage(ignored) : "Chưa chọn file hỗ trợ (.md, .txt, .pptx, .docx, .pdf, audio hoặc video).";
});

$("#create-job").addEventListener("submit", async (event) => {
  event.preventDefault();
  const {supported: files, ignored} = filterSupportedFiles([...$("#source-folder").files]);
  const status = $("#job-status");
  try {
    const request = validateAdminRequest(files, $("#generation-prompt").value);
    const body = new FormData(); body.append("prompt", request.prompt);
    files.forEach((file) => body.append("files", file, file.webkitRelativePath || file.name));
    status.textContent = `Đang upload ${files.length} học liệu và xếp job…${ignored.length ? ` Đã bỏ qua ${ignored.length} file không hỗ trợ.` : ""}`;
    const response = await fetch("/api/admin/jobs", {method: "POST", body});
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || "Không thể tạo job.");
    clearInterval(pollTimer); await pollJob(job.id); pollTimer = setInterval(() => pollJob(job.id), 1500);
  } catch (error) { status.textContent = error.message; }
});

$("#lecture-select").addEventListener("change", (event) => {
  setActiveBundle(event.target.value);
  loadAnalytics(activeBundleId).catch((error) => { $("#analytics-empty").textContent = error.message; });
});

loadPublishedLectures().catch((error) => { $("#analytics-empty").textContent = error.message; });
setInterval(() => { if (activeBundleId) loadAnalytics(activeBundleId).catch(() => {}); }, 5000);
