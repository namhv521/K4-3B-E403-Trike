import {filterSupportedFiles, unsupportedUploadMessage, validateAdminRequest} from "./admin-core.mjs";
import {activityTrend, completionBreakdown, scoreTrend} from "./admin-charts.mjs";

const $ = (selector) => document.querySelector(selector);
const selectedBundleStorageKey = "vlearn-admin-selected-bundle";
let activeBundleId = null;
let pollTimer = null;
const svgNamespace = "http://www.w3.org/2000/svg";

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(svgNamespace, name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
  return element;
}

function replaceChart(selector, label, draw) {
  const host = $(selector);
  host.replaceChildren();
  const chart = svgElement("svg", {viewBox: "0 0 280 150", role: "img", "aria-label": label, focusable: "false"});
  draw(chart);
  host.append(chart);
}

function renderDonutChart(report) {
  const {completed, remaining, rate} = completionBreakdown(report);
  $("#completion-chart-note").textContent = `${completed}/${completed + remaining} phiên đã hoàn thành (${rate}%).`;
  replaceChart("#completion-chart", "Biểu đồ tròn thể hiện tỷ lệ hoàn thành", (chart) => {
    const radius = 48;
    const circumference = 2 * Math.PI * radius;
    chart.append(svgElement("circle", {class: "chart-track", cx: 75, cy: 75, r: radius}));
    if (completed) chart.append(svgElement("circle", {class: "chart-donut", cx: 75, cy: 75, r: radius, "stroke-dasharray": `${(rate / 100) * circumference} ${circumference}`, transform: "rotate(-90 75 75)"}));
    const percentage = svgElement("text", {class: "chart-center-value", x: 75, y: 71, "text-anchor": "middle"}); percentage.textContent = `${rate}%`; chart.append(percentage);
    const caption = svgElement("text", {class: "chart-center-label", x: 75, y: 91, "text-anchor": "middle"}); caption.textContent = "hoàn thành"; chart.append(caption);
    [["Đã hoàn thành", completed, "chart-legend-complete"], ["Chưa hoàn thành", remaining, "chart-legend-remaining"]].forEach(([name, value, className], index) => {
      const y = 56 + index * 28;
      chart.append(svgElement("circle", {class: className, cx: 154, cy: y - 4, r: 5}));
      const text = svgElement("text", {class: "chart-legend", x: 166, y}); text.textContent = `${name}: ${value}`; chart.append(text);
    });
  });
}

function renderTrendChart(selector, noteSelector, series, kind) {
  const empty = kind === "score" ? "Chưa có phiên hoàn thành để vẽ điểm." : "Chưa có hoạt động gần đây để vẽ nhịp học.";
  $(noteSelector).textContent = series.length ? (kind === "score" ? `Hiển thị ${series.length} phiên hoàn thành gần nhất, theo thứ tự thời gian.` : `${series.reduce((sum, point) => sum + point.value, 0)} event được gom theo mốc thời gian.`) : empty;
  replaceChart(selector, kind === "score" ? "Biểu đồ đường điểm theo phiên" : "Biểu đồ miền hoạt động gần đây", (chart) => {
    if (!series.length) { const text = svgElement("text", {class: "chart-empty", x: 140, y: 78, "text-anchor": "middle"}); text.textContent = "Chưa có dữ liệu"; chart.append(text); return; }
    const left = 24, right = 262, top = 18, bottom = 118;
    const maximum = kind === "score" ? 10 : Math.max(1, ...series.map((point) => point.value));
    const points = series.map((point, index) => ({x: series.length === 1 ? (left + right) / 2 : left + (index * (right - left)) / (series.length - 1), y: bottom - (point.value / maximum) * (bottom - top)}));
    [top, (top + bottom) / 2, bottom].forEach((y) => chart.append(svgElement("line", {class: "chart-gridline", x1: left, x2: right, y1: y, y2: y})));
    if (kind === "activity") chart.append(svgElement("path", {class: "chart-area", d: `M ${points[0].x} ${bottom} L ${points.map((point) => `${point.x} ${point.y}`).join(" L ")} L ${points.at(-1).x} ${bottom} Z`}));
    chart.append(svgElement("polyline", {class: kind === "score" ? "chart-line chart-line-score" : "chart-line chart-line-activity", points: points.map((point) => `${point.x},${point.y}`).join(" ")}));
    points.forEach((point, index) => {
      chart.append(svgElement("circle", {class: kind === "score" ? "chart-point-score" : "chart-point-activity", cx: point.x, cy: point.y, r: 3.5}));
      const label = svgElement("text", {class: "chart-axis-label", x: point.x, y: 140, "text-anchor": "middle"}); label.textContent = series[index].label; chart.append(label);
    });
  });
}

function renderCharts(report) {
  renderDonutChart(report);
  renderTrendChart("#score-chart", "#score-chart-note", scoreTrend(report.sessions), "score");
  renderTrendChart("#activity-chart", "#activity-chart-note", activityTrend(report.recent_events), "activity");
}

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
  renderCharts(report);
  renderRows("#checkpoint-analytics", report.checkpoints, (row) => `${row.checkpoint_id}: ${row.first_attempt_accuracy}% đúng lần đầu · ${row.incorrect} lượt sai`, "Chưa có câu trả lời.");
  renderRows("#misconception-analytics", report.misconceptions, (row) => `${row.label || row.misconception_id}: ${row.count} lần`, "Chưa ghi nhận nhầm lẫn.");
  renderRows("#user-analytics", report.users || [], (row) => `${row.user_name} · ${row.completed ? "đã hoàn thành" : "đang học"} · ${row.event_count} log`, "Chưa có user học lecture này.");
  renderRows("#session-analytics", report.sessions, (row) => {
    if (!row.completed) return `${row.session_id.slice(0, 8)}… · đang xem · ${row.event_count} event`;
    const score = typeof row.score === "number" ? `${row.score}/10 điểm` : "chưa có điểm";
    const accuracy = typeof row.first_attempt_accuracy === "number" ? ` · đúng lần đầu ${row.first_attempt_accuracy}%` : "";
    return `${row.session_id.slice(0, 8)}… · ${score}${accuracy} · đã hoàn thành`;
  }, "Chưa có phiên xem.");
  renderRows("#event-analytics", report.recent_events, (row) => {
    const checkpoint = row.checkpoint_id ? ` · ${row.checkpoint_id}` : "";
    const answer = typeof row.is_correct === "boolean" ? ` · ${row.is_correct ? "đúng" : "sai"}` : "";
    const user = row.user_name ? `${row.user_name} · ` : "";
    return `${new Date(row.timestamp).toLocaleTimeString("vi-VN", {hour12: false})} · ${user}${row.session_id.slice(0, 8)}… · ${row.event}${checkpoint}${answer}`;
  }, "Chưa có hoạt động.");
}

function setActiveBundle(bundleId) {
  activeBundleId = bundleId || null;
  if (activeBundleId) localStorage.setItem(selectedBundleStorageKey, activeBundleId);
  else localStorage.removeItem(selectedBundleStorageKey);
}

async function loadPublishedLectures(preferredBundleId = null) {
  const response = await fetch("/api/lectures", {cache: "no-store"});
  if (!response.ok) throw new Error("Không thể tải danh sách lecture.");
  const lectures = await response.json();
  const target = $("#target-lecture-select");
  target.replaceChildren();
  lectures.forEach((lecture) => target.append(new Option(`${lecture.title}${lecture.published ? " · đang có video" : " · trống"}`, lecture.lecture_id)));
  const select = $("#lecture-select");
  select.replaceChildren();
  const published = lectures.filter((lecture) => lecture.published);
  if (!published.length) {
    select.append(new Option("Chưa có lecture được publish", ""));
    select.disabled = true;
    setActiveBundle(null);
    $("#analytics").hidden = true;
    $("#analytics-empty").hidden = false;
    return;
  }
  published.forEach((lecture) => {
    select.append(new Option(`${lecture.title} · ${lecture.lesson_title} · ${lecture.checkpoint_count} checkpoint`, lecture.lecture_id));
  });
  select.disabled = false;
  const available = new Set(published.map((lecture) => lecture.lecture_id));
  const chosen = [preferredBundleId, activeBundleId, localStorage.getItem(selectedBundleStorageKey), published[0].lecture_id]
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
    body.append("lecture_id", $("#target-lecture-select").value);
    status.textContent = `Đang upload ${files.length} học liệu và xếp job…${ignored.length ? ` Đã bỏ qua ${ignored.length} file không hỗ trợ.` : ""}`;
    const response = await fetch("/api/admin/jobs", {method: "POST", body});
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || "Không thể tạo job.");
    clearInterval(pollTimer); await pollJob(job.id); pollTimer = setInterval(() => pollJob(job.id), 1500);
  } catch (error) { status.textContent = error.message; }
});

async function loadUsers() {
  const response = await fetch("/api/users", {cache: "no-store"});
  if (!response.ok) throw new Error("Không thể tải user local.");
  const users = await response.json();
  renderRows("#admin-user-list", users, (user) => `${user.name} · ${user.id === "demo-user" ? "user demo" : "user đã tạo"}`, "Chưa có user.");
}

$("#create-user").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = $("#user-status");
  try {
    const response = await fetch("/api/admin/users", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({name: $("#new-user-name").value})});
    const user = await response.json();
    if (!response.ok) throw new Error(user.error || "Không thể tạo user.");
    $("#new-user-name").value = "";
    status.textContent = `Đã tạo ${user.name}. Chuyển sang User để chọn role này.`;
    await loadUsers();
  } catch (error) { status.textContent = error.message; }
});

$("#lecture-select").addEventListener("change", (event) => {
  setActiveBundle(event.target.value);
  loadAnalytics(activeBundleId).catch((error) => { $("#analytics-empty").textContent = error.message; });
});

loadPublishedLectures().catch((error) => { $("#analytics-empty").textContent = error.message; });
loadUsers().catch((error) => { $("#user-status").textContent = error.message; });
setInterval(() => { if (activeBundleId) loadAnalytics(activeBundleId).catch(() => {}); }, 5000);
