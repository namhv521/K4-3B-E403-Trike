import assert from "node:assert/strict";
import test from "node:test";
import {filterSupportedFiles, unsupportedUploadMessage, validateAdminRequest} from "../admin-core.mjs";

test("admin request requires a meaningful prompt and at least one source file", () => {
  assert.throws(() => validateAdminRequest([], "Tạo recap"), /ít nhất một/);
  assert.throws(() => validateAdminRequest([{name: "lesson.pdf"}], "ngắn"), /8/);
  assert.deepEqual(validateAdminRequest([{name: "slides/lesson.pdf"}], "Tạo video recap 60 giây"), {file_count: 1, prompt: "Tạo video recap 60 giây"});
});

test("admin filters unsupported files selected from a folder", () => {
  const result = filterSupportedFiles([
    {name: "lesson.md"},
    {name: "slides/week-1.pptx"},
    {name: "documents/handout.docx"},
    {name: "Thumbs.db"},
    {name: "tools/setup.exe"},
  ]);

  assert.deepEqual(result.supported.map((file) => file.name), ["lesson.md", "slides/week-1.pptx", "documents/handout.docx"]);
  assert.deepEqual(result.ignored.map((file) => file.name), ["Thumbs.db", "tools/setup.exe"]);
});

test("admin explains that legacy PowerPoint files must be saved as PPTX", () => {
  assert.equal(
    unsupportedUploadMessage([{name: "slides/lecture-1.ppt"}]),
    "File PowerPoint .ppt cũ chưa được hỗ trợ. Hãy mở và lưu lại thành .pptx trước khi tạo video.",
  );
});
