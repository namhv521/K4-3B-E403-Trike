const SUPPORTED_UPLOAD_EXTENSIONS = new Set([".md", ".txt", ".pptx", ".docx", ".pdf", ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp4", ".mov", ".webm", ".mkv"]);

function uploadName(file) {
  return file.webkitRelativePath || file.name || "";
}

function uploadExtension(file) {
  return /\.[^.\\/]+$/.exec(uploadName(file))?.[0]?.toLowerCase();
}

export function filterSupportedFiles(files) {
  const supported = [];
  const ignored = [];
  for (const file of files || []) {
    (SUPPORTED_UPLOAD_EXTENSIONS.has(uploadExtension(file)) ? supported : ignored).push(file);
  }
  return {supported, ignored};
}

export function unsupportedUploadMessage(files) {
  if ((files || []).some((file) => uploadExtension(file) === ".ppt")) {
    return "File PowerPoint .ppt cũ chưa được hỗ trợ. Hãy mở và lưu lại thành .pptx trước khi tạo video.";
  }
  return "Chỉ nhận học liệu hỗ trợ (.md, .txt, .pptx, .docx, .pdf, audio hoặc video).";
}

export function validateAdminRequest(files, prompt) {
  const cleanPrompt = String(prompt || "").trim();
  if (!files?.length) throw new Error("Hãy chọn ít nhất một học liệu.");
  if (cleanPrompt.length < 8 || cleanPrompt.length > 500) throw new Error("Prompt cần từ 8 đến 500 ký tự.");
  return {file_count: files.length, prompt: cleanPrompt};
}
