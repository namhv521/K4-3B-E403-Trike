export function validateAdminRequest(files, prompt) {
  const cleanPrompt = String(prompt || "").trim();
  if (!files?.length) throw new Error("Hãy chọn ít nhất một học liệu.");
  if (cleanPrompt.length < 8 || cleanPrompt.length > 500) throw new Error("Prompt cần từ 8 đến 500 ký tự.");
  return {file_count: files.length, prompt: cleanPrompt};
}
