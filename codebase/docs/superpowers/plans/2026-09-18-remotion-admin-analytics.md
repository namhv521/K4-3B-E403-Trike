# Remotion Admin and Learning Analytics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local admin/user web prototype that generates grounded Remotion recap bundles and aggregates anonymous checkpoint learning telemetry.

**Architecture:** Keep the Python content pipeline as the trust boundary, add an internal generic Remotion renderer, and extend the localhost website server into a small API plus two static role pages. The learner player reads bundle-specific URLs; the admin page orchestrates local jobs and displays aggregated allowlisted events.

**Tech Stack:** Python 3 standard-library HTTP server and unittest; existing Python generator/Edge TTS; internal TypeScript React/Remotion v4 project; vanilla HTML/CSS/ES modules; Node test runner.

**Spec:** `codebase/docs/superpowers/specs/2026-09-18-remotion-admin-analytics-design.md`

## Global Constraints

- Preserve `lesson.json` citations, checkpoint timecodes and validation rules.
- Keep API keys, source text and user identity out of browser and telemetry.
- Bind the local service to `127.0.0.1`; label roles/auth as prototype-only.
- Use only allowlisted telemetry fields and no public leaderboard/official grade.
- Render actual media duration and reject unpublished invalid bundles.

---

### Task 1: Generic Remotion recap renderer

**Files:**
- Create: `codebase/video-generator/remotion-recap/package.json`
- Create: `codebase/video-generator/remotion-recap/src/Root.tsx`
- Create: `codebase/video-generator/remotion-recap/src/Recap.tsx`
- Create: `codebase/video-generator/remotion-recap/src/types.ts`
- Create: `codebase/video-generator/remotion-recap/src/index.ts`
- Create: `codebase/video-generator/tests/test_remotion_renderer.py`
- Modify: `codebase/video-generator/render_video.py`

**Interfaces:**
- Consumes: validated `lesson` and narration file path.
- Produces: `render_video(lesson, narration_path, output_path)` MP4 with lesson duration.

- [ ] Write a failing test that expects the renderer command to include the
  generic composition id, JSON props and output path.
- [ ] Run `python -m unittest tests.test_remotion_renderer -v` and verify it
  fails because the adapter does not exist.
- [ ] Add a minimal adapter that invokes `npx remotion render VLearnRecap` with
  only JSON-serializable lesson props and validates output existence.
- [ ] Create a generic `Series` Composition that renders scene title/body,
  scene-aligned audio, subtitle chunks and non-Docker VLearn styling.
- [ ] Run the test and verify it passes; keep FFmpeg/Pillow renderer as an
  explicit fallback only when `VLEARN_RENDERER=ffmpeg` is selected.
- [ ] Commit the renderer task.

### Task 2: Job and telemetry service

**Files:**
- Create: `codebase/interactive-website/service.py`
- Create: `codebase/interactive-website/tests/test_service.py`
- Modify: `codebase/interactive-website/server.py`

**Interfaces:**
- `JobStore.create(files, prompt) -> job_id`
- `TelemetryStore.append(bundle_id, event) -> event`
- `analytics(bundle_id) -> dict`

- [ ] Write failing tests for unsupported upload rejection, secret stripping,
  checkpoint/misconception aggregation and local-only path traversal rejection.
- [ ] Run `python -m unittest tests.test_service -v` and verify failures are
  for the missing service contracts.
- [ ] Implement stores using `runtime/` paths, UUID ids, atomic JSON writes,
  JSONL append and the existing event allowlist.
- [ ] Extend the existing local server with multipart upload, job lookup,
  bundle delivery, telemetry POST and analytics GET routes; return JSON errors
  without source text.
- [ ] Run service tests and verify they pass.
- [ ] Commit the service task.

### Task 3: Admin console

**Files:**
- Create: `codebase/interactive-website/admin.html`
- Create: `codebase/interactive-website/admin.js`
- Modify: `codebase/interactive-website/styles.css`
- Modify: `codebase/interactive-website/index.html`

**Interfaces:**
- Consumes: `POST /api/admin/jobs`, job status and analytics JSON.
- Produces: local admin upload, progress and aggregate misconception display.

- [ ] Write a failing browser-independent test for admin payload validation
  (prompt length and empty folder rejection).
- [ ] Run the web test command and verify the test fails before helper exists.
- [ ] Implement folder picker (`webkitdirectory`), upload/progress state,
  explicit local-prototype notice, bundle list and dashboard rows sorted by
  error count.
- [ ] Render an actionable message naming the most-error checkpoint and its
  misconception without identifying learners.
- [ ] Run web tests, syntax checks and inspect desktop/mobile layout once.
- [ ] Commit the admin task.

### Task 4: Bundle-aware learner page and telemetry transport

**Files:**
- Modify: `codebase/interactive-website/app.js`
- Modify: `codebase/interactive-website/core.mjs`
- Modify: `codebase/interactive-website/index.html`
- Modify: `codebase/interactive-website/tests/test_core.mjs`

**Interfaces:**
- Consumes: bundle id from `/learn/<id>` and `/api/bundles/<id>/*` assets.
- Produces: best-effort allowlisted `POST /api/events` alongside local log.

- [ ] Write failing tests that reject telemetry fields outside the allowlist and
  preserve existing completion/fast-view metrics.
- [ ] Run `node --test tests/test_core.mjs` and observe the expected failure.
- [ ] Resolve assets from bundle metadata while retaining fixture fallback;
  use `navigator.sendBeacon`/`fetch` for local telemetry without blocking
  learning when service transport fails.
- [ ] Keep all current checkpoint control, source display, live log, answer
  states and final result metrics unchanged.
- [ ] Run tests and manual smoke test a correct answer, wrong answer, seek,
  completion and exported log.
- [ ] Commit the learner task.

### Task 5: Documentation and regression verification

**Files:**
- Modify: `codebase/README.md`
- Modify: `codebase/video-generator/README.md`
- Modify: `codebase/interactive-website/README.md`

- [ ] Document local startup, admin flow, required Remotion/Node setup, mock
  labels, security boundary and known production gaps.
- [ ] Run all generator, website and desktop suites.
- [ ] Run one fixture generation/render smoke test and verify the generated
  bundle opens through `/learn/<bundle-id>`.
- [ ] Commit documentation and verification updates.
