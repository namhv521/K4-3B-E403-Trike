import assert from "node:assert/strict";
import test from "node:test";
import {validateAdminRequest} from "../admin-core.mjs";

test("admin request requires a meaningful prompt and at least one source file", () => {
  assert.throws(() => validateAdminRequest([], "Tạo recap"), /ít nhất một/);
  assert.throws(() => validateAdminRequest([{name: "lesson.pdf"}], "ngắn"), /8/);
  assert.deepEqual(validateAdminRequest([{name: "slides/lesson.pdf"}], "Tạo video recap 60 giây"), {file_count: 1, prompt: "Tạo video recap 60 giây"});
});
