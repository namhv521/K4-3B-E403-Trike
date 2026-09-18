import {validateAdminRequest} from "./admin-core.mjs";

const $ = (selector) => document.querySelector(selector);
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
  if (!response.ok) return;
  const report = await response.json();
  $("#analytics-empty").hidden = true; $("#analytics").hidden = false;
  $("#metric-views").textContent = report.views;
  $("#metric-completed").textContent = report.completed_sessions;
  $("#metric-fast").textContent = report.fast_completion_count;
  renderRows("#checkpoint-analytics", report.checkpoints, (row) => `${row.checkpoint_id}: ${row.first_attempt_accuracy}% đúng lần đầu · ${row.incorrect} lượt sai`, "Chưa có câu trả lời.");
  renderRows("#misconception-analytics", report.misconceptions, (row) => `${row.label || row.misconception_id}: ${row.count} lần`, "Chưa ghi nhận nhầm lẫn.");
}

async function pollJob(jobId) {
  const response = await fetch(`/api/admin/jobs/${jobId}`, {cache: "no-store"});
  const job = await response.json();
  const status = $("#job-status");
  if (!response.ok) { status.textContent = job.error || "Không đọc được job."; return; }
  status.textContent = `Job ${job.status}${job.error ? `: ${job.error}` : ""}`;
  if (job.status === "succeeded") {
    clearInterval(pollTimer); pollTimer = null; activeBundleId = job.bundle_id;
    const link = $("#bundle-link"); link.href = job.bundle_url; link.hidden = false;
    loadAnalytics(activeBundleId); return;
  }
  if (job.status === "failed") { clearInterval(pollTimer); pollTimer = null; }
}

$("#source-folder").addEventListener("change", (event) => {
  const files = [...event.target.files];
  $("#file-count").textContent = files.length ? `${files.length} file được chọn` : "Chưa chọn file";
});

$("#create-job").addEventListener("submit", async (event) => {
  event.preventDefault();
  const files = [...$("#source-folder").files];
  const status = $("#job-status");
  try {
    const request = validateAdminRequest(files, $("#generation-prompt").value);
    const body = new FormData(); body.append("prompt", request.prompt);
    files.forEach((file) => body.append("files", file, file.webkitRelativePath || file.name));
    status.textContent = "Đang upload học liệu và xếp job…";
    const response = await fetch("/api/admin/jobs", {method: "POST", body});
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || "Không thể tạo job.");
    clearInterval(pollTimer); await pollJob(job.id); pollTimer = setInterval(() => pollJob(job.id), 1500);
  } catch (error) { status.textContent = error.message; }
});

setInterval(() => { if (activeBundleId) loadAnalytics(activeBundleId); }, 5000);
