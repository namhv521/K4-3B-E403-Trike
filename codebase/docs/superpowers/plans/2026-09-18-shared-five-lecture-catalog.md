# Shared Five-Lecture Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide the same persistent, continuously refreshed catalogue of Lecture 1 through Lecture 5 to learner and admin roles, seed the current demo video into Lecture 1, and let Admin replace a selected lecture's video through the existing generation workflow.

**Architecture:** `JobStore` owns a fixed five-record catalogue and persists published artifacts under stable bundle IDs (`lecture1` through `lecture5`) within the existing local `runtime/` storage. The server exposes one public catalogue response used by both pages; learner telemetry remains keyed by this same stable lecture ID in the existing JSONL telemetry database. A generation job retains a UUID for job status but records its target `lecture_id`, renders into job-local staging, then atomically publishes the three validated artifacts to that lecture so a failed replacement cannot remove the currently playable video.

**Tech Stack:** Python 3.12 standard-library HTTP server and `unittest`; vanilla HTML, CSS and ES modules; Node 20 built-in test runner; existing Python/Remotion generation pipeline.

**Spec:** `C:\Su\VinLab\Hackathon\codebase\docs\superpowers\specs\2026-09-18-remotion-admin-analytics-design.md` (extended by the user's fixed five-lecture catalogue request on 2026-09-18)

## Global Constraints

- The only lecture IDs are exactly `lecture1`, `lecture2`, `lecture3`, `lecture4` and `lecture5`; no browser input can select an arbitrary path.
- `lesson.json` remains the source of truth for lesson content, citations, checkpoint timecodes, answers and misconceptions.
- Reuse the current `assets/lesson.json`, `assets/sources.json` and `assets/recap.mp4` only to seed `lecture1`; never expose source uploads or generation prompts.
- Keep job staging, published bundles and telemetry under the existing local `runtime/` root; both role pages consume the same server state and telemetry JSONL database.
- A learner event may be ingested only for a fully published lecture bundle and through the existing telemetry allowlist.
- A replacement generation failure must leave the last published lecture bundle playable.
- Bind only to `127.0.0.1`, retain the local-prototype notice, and do not add identity, login, ranking or gradebook behavior.
- Use no additional packages or frameworks.

---

### Task 1: Stable five-lecture persistence and safe publication

**Files:**
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\service.py:14-143`
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\tests\test_service.py:113-151`

**Interfaces:**
- Consumes: `JobStore(runtime_root)` and the existing three asset files supplied as `asset_root` during startup.
- Produces: `LECTURE_IDS: tuple[str, ...]`, `JobStore.list_lectures() -> list[dict]`, `JobStore.ensure_lecture_one(asset_root: Path) -> None`, `JobStore.create(prompt: str, files: list[tuple[str, bytes]], lecture_id: str) -> dict`, and `JobStore.run(job_id: str, generator_dir: Path) -> dict`.
- Lecture response row shape: `{"lecture_id": "lecture1", "title": "Lecture 1", "published": True, "lesson_title": "...", "checkpoint_count": 3, "bundle_url": "/learn/lecture1"}`. Unpublished rows omit `lesson_title` and have `checkpoint_count: 0`.

- [ ] **Step 1: Write the failing fixed-catalogue and bootstrap tests**

Add a test that constructs `JobStore(Path(folder))`, creates a temporary `assets` directory containing non-empty `lesson.json`, `sources.json` and `recap.mp4`, calls `ensure_lecture_one(assets)`, and asserts that `list_lectures()` returns exactly the IDs below in this order and marks only `lecture1` published:

```python
self.assertEqual([row["lecture_id"] for row in jobs.list_lectures()], [
    "lecture1", "lecture2", "lecture3", "lecture4", "lecture5",
])
self.assertTrue(jobs.list_lectures()[0]["published"])
self.assertFalse(any(row["published"] for row in jobs.list_lectures()[1:]))
self.assertEqual((jobs.bundle_dir("lecture1") / "recap.mp4").read_bytes(), b"demo video")
```

Add a second test that calls `jobs.create("Tạo video recap 60 giây", [("lesson.md", b"Noi dung")], "lecture3")` and asserts `job["lecture_id"] == "lecture3"`, `job["bundle_id"] == "lecture3"`, and that `jobs.create(..., "not-a-lecture")` raises `ValueError` containing `Lecture`.

- [ ] **Step 2: Run the focused tests to verify failure**

Run:

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase\interactive-website'
python -m unittest tests.test_service.ServiceTests.test_job_store_bootstraps_the_fixed_shared_lecture_catalog tests.test_service.ServiceTests.test_job_store_assigns_jobs_only_to_fixed_lectures -v
```

Expected: FAIL because the new methods and `lecture_id` argument do not exist.

- [ ] **Step 3: Define the fixed IDs and validate them at the service boundary**

Near the existing upload allowlist add:

```python
LECTURE_IDS = ("lecture1", "lecture2", "lecture3", "lecture4", "lecture5")

def validate_lecture_id(lecture_id):
    if lecture_id not in LECTURE_IDS:
        raise ValueError("Lecture không hợp lệ.")
    return lecture_id
```

Use `validate_lecture_id()` in `bundle_dir()` so asset delivery, event validation, jobs and catalogue entries share exactly one trusted ID set. Preserve the existing traversal checks as defense in depth.

- [ ] **Step 4: Implement bootstrap and common catalogue serialization**

Add `ensure_lecture_one(self, asset_root)` which returns without copying when the three target files already form a published `lecture1`; otherwise validates that each source asset is a non-empty file, copies all three to `runtime/bundles/.lecture1-seed`, and renames that completed directory to `runtime/bundles/lecture1`. Do not overwrite an existing published Lecture 1.

Replace `list_published_bundles()` with `list_lectures()`. Iterate `LECTURE_IDS` rather than runtime directory names, always emit five rows, inspect only the three expected artifacts, and safely read title/checkpoint count only for a valid published bundle. Keep a compatibility `list_published_bundles()` wrapper only if a remaining internal caller needs the old narrow shape; migrate callers in Task 2 instead.

- [ ] **Step 5: Associate each job with a lecture and publish via staging**

Change the creation signature to `create(self, prompt, files, lecture_id)`, validate `lecture_id` before writing files, write `{"prompt": prompt, "lecture_id": lecture_id}` only in job-private `request.json`, and return this public/redacted status:

```python
{"id": job_id, "status": "queued", "lecture_id": lecture_id, "bundle_id": lecture_id}
```

In `run()`, render to `runtime/jobs/<job-id>/output` instead of `runtime/bundles/<lecture-id>`. After validating the three non-empty artifacts, publish under a `threading.Lock`: rename an existing target to a same-parent backup name, rename the complete staging directory to `runtime/bundles/<lecture-id>`, then remove the backup. On validation/render failure, remove staging only; never remove an old published target. Return `bundle_url=f"/learn/{lecture_id}"` only after publish succeeds. Continue deleting input and prompt request in `finally`.

- [ ] **Step 6: Run service tests to verify persistence behavior**

Run:

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase\interactive-website'
python -m unittest tests.test_service -v
```

Expected: PASS, including existing upload, telemetry, analytics and publication tests after their expected metadata has been updated from arbitrary bundle names to fixed lecture IDs.

- [ ] **Step 7: Commit the isolated storage contract**

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase'
git add interactive-website/service.py interactive-website/tests/test_service.py
git commit -m "feat: add persistent five-lecture catalog"
```

### Task 2: Shared catalogue HTTP API and lecture-targeted jobs

**Files:**
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\server.py:12-134`
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\tests\test_service.py:113-151`

**Interfaces:**
- Consumes: `JOBS.ensure_lecture_one(ROOT / "assets")`, `JOBS.list_lectures()` and `JOBS.create(prompt, files, lecture_id)` from Task 1.
- Produces: `GET /api/lectures -> list[LectureRow]`; `GET /api/admin/lectures -> list[LectureRow]` as an explicit admin alias if needed by existing UI; `POST /api/admin/jobs` requiring multipart field `lecture_id`.

- [ ] **Step 1: Write the failing server-contract test**

Add a service-level assertion that the serializable lecture row produced after bootstrap has only safe public fields and exposes the stable learner URL:

```python
self.assertEqual(lectures[0], {
    "lecture_id": "lecture1", "title": "Lecture 1", "published": True,
    "lesson_title": "Demo lesson", "checkpoint_count": 1,
    "bundle_url": "/learn/lecture1",
})
```

This test guards the exact API contract without starting an HTTP server.

- [ ] **Step 2: Run the targeted test and verify it fails**

Run:

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase\interactive-website'
python -m unittest tests.test_service.ServiceTests.test_job_store_bootstraps_the_fixed_shared_lecture_catalog -v
```

Expected: FAIL until `list_lectures()` includes safe public metadata and URL.

- [ ] **Step 3: Initialize Lecture 1 exactly once during server startup**

Immediately after `JOBS = JobStore(RUNTIME)`, invoke:

```python
JOBS.ensure_lecture_one(ROOT / "assets")
```

Do not seed through an HTTP request and do not copy the demo assets on every request. A later Admin publication for Lecture 1 must remain intact across restarts because bootstrap skips a complete published target.

- [ ] **Step 4: Expose the one shared catalogue and require target lecture on uploads**

In `do_GET`, return `JOBS.list_lectures()` for `/api/lectures`. Point the existing `/api/admin/bundles` route to the same rows temporarily only if needed during the frontend migration, then remove it once no caller remains. In `_post_job`, pass `form.getfirst("lecture_id", "")` as the third `JOBS.create()` argument. Invalid/missing IDs must return the existing 400 JSON error, not select a default lecture silently.

Leave `/learn/<lecture-id>`, bundle asset routes and `/api/events` on `bundle_dir()` validation so they naturally reject IDs outside the five-record catalogue and accept only completed bundles for telemetry.

- [ ] **Step 5: Run the service suite and HTTP syntax check**

Run:

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase\interactive-website'
python -m unittest tests.test_service -v
python -m py_compile service.py server.py
```

Expected: PASS and no compiler output.

- [ ] **Step 6: Commit the HTTP contract**

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase'
git add interactive-website/server.py interactive-website/service.py interactive-website/tests/test_service.py
git commit -m "feat: expose shared lecture catalog API"
```

### Task 3: Admin target selector and explicit Tạo lecture action

**Files:**
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\admin-core.mjs:1-22`
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\tests\test_admin_core.mjs:1-22`
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\admin.html:12-41`
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\admin.js:1-119`
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\styles.css:82-99`

**Interfaces:**
- Consumes: `GET /api/lectures`, `POST /api/admin/jobs` multipart fields `files`, `prompt`, `lecture_id`, and `GET /api/admin/analytics?bundle_id=<lecture-id>`.
- Produces: `validateAdminRequest(files, prompt, lectureId) -> {file_count, prompt, lecture_id}` and an Admin page which renders all five shared lecture rows, chooses one target, then posts the target with the generation request.

- [ ] **Step 1: Write a failing frontend-independent target validation test**

Extend `test_admin_core.mjs` with:

```javascript
assert.throws(
  () => validateAdminRequest([{name: "lesson.pdf"}], "Tạo video recap 60 giây", "lecture99"),
  /Lecture/,
);
assert.deepEqual(
  validateAdminRequest([{name: "lesson.pdf"}], "Tạo video recap 60 giây", "lecture4"),
  {file_count: 1, prompt: "Tạo video recap 60 giây", lecture_id: "lecture4"},
);
```

- [ ] **Step 2: Run Node tests and verify the new case fails**

Run:

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase\interactive-website'
node --test tests/test_admin_core.mjs
```

Expected: FAIL because `validateAdminRequest` currently accepts only two arguments and returns no target.

- [ ] **Step 3: Validate only fixed lecture target IDs in browser helper**

Add `const LECTURE_IDS = new Set(["lecture1", "lecture2", "lecture3", "lecture4", "lecture5"]);` in `admin-core.mjs`. Make `validateAdminRequest(files, prompt, lectureId)` retain current prompt/file validation, reject missing or non-catalogue ID with `new Error("Lecture không hợp lệ.")`, and return `lecture_id` with the existing fields. Server validation from Task 1 remains authoritative.

- [ ] **Step 4: Add catalogue and target controls to Admin markup**

Above the source folder field, add a `label` and `select#target-lecture-select` named `lecture_id`, initially disabled with five-loading text. Add a short status element explaining that the completed video will replace the selected lecture. Change the existing submit control text from `Tạo bundle Remotion` to **`Tạo lecture`**; this is the requested explicit Admin action and starts a generation job for the selected target, not a sixth lecture. Retain `#lecture-select` for dashboard selection, but relabel it as analytics only.

Add an Admin catalogue section/list (`#lecture-catalog`) with five rows showing `Lecture N`, published/unpublished state, lesson title/checkpoint count when available, and a learner link only when published. This gives the role an always-visible shared list rather than only a filtered published list.

- [ ] **Step 5: Load one catalogue into both Admin selectors and poll it**

Replace `loadPublishedLectures()` with `loadLectures(preferredLectureId = null)`, fetching `/api/lectures` with `{cache: "no-store"}`. Populate `#target-lecture-select` with all five records and populate dashboard `#lecture-select` with all five records, preserving current selections and `localStorage` state by `lecture_id`. When a dashboard lecture is unpublished, show the empty dashboard guidance rather than requesting analytics for an unavailable video. When a job succeeds, set its target as both selected lecture and target selector, show `job.bundle_url`, then refresh the shared catalogue.

In form submission, call:

```javascript
const request = validateAdminRequest(files, $("#generation-prompt").value, $("#target-lecture-select").value);
body.append("lecture_id", request.lecture_id);
```

Add one five-second interval which calls `loadLectures()` and, for a published active lecture, `loadAnalytics(activeBundleId)`. Avoid starting duplicate intervals while a job is polling.

- [ ] **Step 6: Style the catalogue without changing desktop/mobile conventions**

Use existing color variables and introduce focused rules for `.lecture-catalog`, `.lecture-catalog li`, and `.lecture-status`. Keep select controls full width, sufficient contrast for unpublished state, and collapse rows naturally under the existing 650px media query. Do not introduce a component library.

- [ ] **Step 7: Verify Admin unit tests and module syntax**

Run:

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase\interactive-website'
node --test tests/test_admin_core.mjs
node --check admin.js
```

Expected: all tests PASS and syntax checks emit no output.

- [ ] **Step 8: Commit the Admin workflow**

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase'
git add interactive-website/admin-core.mjs interactive-website/tests/test_admin_core.mjs interactive-website/admin.html interactive-website/admin.js interactive-website/styles.css
git commit -m "feat: target generated videos to shared lectures"
```

### Task 4: Learner shared list and non-disruptive live synchronization

**Files:**
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\index.html:11-23`
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\app.js:1-112`
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\styles.css:20-30,99`
- Modify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\README.md:42-63`

**Interfaces:**
- Consumes: `GET /api/lectures -> list[LectureRow]`, stable learner links `/learn/<lecture-id>`, and existing `/api/bundles/<lecture-id>/{lesson.json,sources.json,recap.mp4}` assets.
- Produces: learner UI list `#learner-lecture-list`, selected `#learner-lecture-select`, and bundle loading by a fixed published `lecture_id` (default `lecture1`).

- [ ] **Step 1: Add learner catalogue markup that remains accessible**

Under the learner header, add a `section` labelled “Danh sách lecture”, a `select#learner-lecture-select` with a disabled loading option, and `ul#learner-lecture-list`. Each row must include the lecture display title and clear `Đã có video`/`Chưa có video` status. Keep the current player structure and all checkpoint elements unchanged.

- [ ] **Step 2: Make Lecture 1 the default learner target and fetch common metadata**

Change the startup ID expression to:

```javascript
const requestedLectureId = new URLSearchParams(location.search).get("bundle") || "lecture1";
let bundleId = requestedLectureId;
```

Build asset paths only after `/api/lectures` confirms the selected row is published. Fetch the catalogue with `cache: "no-store"`, populate the select/list from every returned row, and navigate with `location.assign(`/learn/${encodeURIComponent(lectureId)}`)` when the learner selects a published lecture. Disable unavailable options and show an explicit status for an unpublished selection; never attempt to fetch non-existent assets.

- [ ] **Step 3: Poll shared catalogue safely**

Every five seconds, refetch `/api/lectures` and update status/list text in place. Do not reload or replace the current player merely because metadata changes; only user selection navigates to a different lecture. If the active lecture becomes unavailable unexpectedly, stop telemetry sends and show a retry message rather than crashing the live learning session.

Keep `sendEvent()` exactly bundle-scoped, now using the stable current lecture ID. This means User completion and Admin analytics merge continuously through the same `runtime/telemetry/events.jsonl` record keys.

- [ ] **Step 4: Apply responsive list/select styles**

Add a compact `.lecture-picker` presentation near existing lesson header styles, reuse `.lecture-status` from Task 3 where appropriate, and ensure focus-visible works for the new select. On narrow layouts, retain the existing vertical header behavior.

- [ ] **Step 5: Document stable learner links and shared-storage behavior**

Update `interactive-website/README.md` role instructions to state:

```text
Lecture 1 through Lecture 5 are a fixed shared local catalogue. The current demo
assets seed Lecture 1 on server startup. Admin selects a target lecture before
creating it; users open /learn/lecture1 through /learn/lecture5. Both pages
poll the same runtime catalogue and analytics remain anonymous by lecture.
```

Also state that only published entries can be played and that a re-render replaces the selected lecture after successful validation.

- [ ] **Step 6: Verify learner module syntax and existing core regression tests**

Run:

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase\interactive-website'
node --test tests/test_core.mjs tests/test_admin_core.mjs
node --check app.js
node --check admin.js
```

Expected: PASS and no syntax output.

- [ ] **Step 7: Commit learner catalogue synchronization**

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase'
git add interactive-website/index.html interactive-website/app.js interactive-website/styles.css interactive-website/README.md
git commit -m "feat: show shared lectures to learners"
```

### Task 5: End-to-end verification and documentation completion

**Files:**
- Modify if needed after verification: `C:\Su\VinLab\Hackathon\codebase\interactive-website\README.md`
- Verify: `C:\Su\VinLab\Hackathon\codebase\interactive-website\runtime\bundles\lecture1\`

**Interfaces:**
- Consumes the complete API and UI contracts from Tasks 1–4.
- Produces verified local behavior: shared five rows, Lecture 1 playable, only targeted job replacement, and lecture-keyed anonymous analytics.

- [ ] **Step 1: Run all automated project checks**

Run:

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase\interactive-website'
python -m unittest discover -s tests -v
node --test tests/test_core.mjs tests/test_admin_core.mjs
python -m py_compile service.py server.py
node --check app.js
node --check admin.js
git diff --check
```

Expected: every test passes, compilers/syntax checks emit no errors, and `git diff --check` is empty.

- [ ] **Step 2: Run a local HTTP smoke test against a fresh server**

In one non-interactive PowerShell command, start `python server.py --port 8000` as a background process, then assert all required common data:

```powershell
$server = Start-Process python -ArgumentList 'server.py','--port','8000' -WorkingDirectory 'C:\Su\VinLab\Hackathon\codebase\interactive-website' -PassThru
try {
  Start-Sleep -Seconds 1
  $lectures = Invoke-RestMethod 'http://127.0.0.1:8000/api/lectures'
  if (($lectures.lecture_id -join ',') -ne 'lecture1,lecture2,lecture3,lecture4,lecture5') { throw 'Catalogue is not fixed or ordered.' }
  if (-not $lectures[0].published) { throw 'Lecture 1 was not seeded.' }
  $asset = Invoke-WebRequest 'http://127.0.0.1:8000/api/bundles/lecture1/recap.mp4'
  if ($asset.StatusCode -ne 200) { throw 'Lecture 1 video is unavailable.' }
  (Invoke-WebRequest 'http://127.0.0.1:8000/learn/lecture1' -MaximumRedirection 0 -ErrorAction SilentlyContinue).StatusCode
} finally {
  Stop-Process -Id $server.Id -ErrorAction SilentlyContinue
}
```

Expected: catalogue IDs are exactly ordered, Lecture 1 is published, the video returns 200, and `/learn/lecture1` redirects to `/?bundle=lecture1`.

- [ ] **Step 3: Manually verify the two live UIs**

Start the server using `python server.py --port 8000`, then confirm the following browser-visible results:

1. `/` shows Lecture 1–5; Lecture 1 is marked available and begins the current demo video/checkpoints.
2. `/admin` shows the same five entries in both target and analytics controls, plus the explicit **Tạo lecture** button.
3. Choose Lecture 2, choose valid sources, submit **Tạo lecture**, and verify the submitted multipart target is `lecture2`; once its job succeeds, Admin and User lists show Lecture 2 as published without a manual refresh.
4. Complete a checkpoint from `/learn/lecture1`; within five seconds the Admin Lecture 1 dashboard displays the new anonymous view/event/score metrics and does not show it under Lecture 2.

- [ ] **Step 4: Commit verification/documentation only after all checks pass**

```powershell
Set-Location 'C:\Su\VinLab\Hackathon\codebase'
git add interactive-website/README.md
git commit -m "docs: document shared lecture workflow"
git status --short
```

Expected: no uncommitted files belonging to this feature. Do not include unrelated local modifications from other work.

## Self-Review

### Spec coverage

- Fixed shared five-lecture list: Task 1 creates canonical IDs and complete rows; Tasks 3 and 4 render the same `/api/lectures` response.
- One persistent database/state source: Task 1 keeps bundles and telemetry in `runtime/`; Task 4 sends telemetry by the stable selected lecture ID.
- Existing video in Lecture 1: Task 1 bootstrap and Task 2 server-start initialization copy the three existing asset artifacts once.
- Admin chooses target lecture: Task 3 validates and posts `lecture_id`; Task 2 validates it server-side; Task 1 publishes to that stable directory.
- Admin Tạo lecture button: Task 3 changes the job submit action explicitly to `Tạo lecture` and documents that it replaces the selected fixed slot.
- Continuous cross-role updates: Task 3 and Task 4 poll `/api/lectures` every five seconds; analytics keeps its existing polling keyed by the same stable ID.
- Safe replacement: Task 1 stages renderer output and atomically swaps it only after validation; failure preserves prior bundle.
- Existing analytics/privacy constraints: Tasks 1, 2 and 4 retain validated allowlisted telemetry, stable anonymous IDs, no browser secrets and local-only service.

### Placeholder scan

No task contains TODO/TBD or an unspecified test. Every code-facing task identifies files, exact function/API contracts, commands, expected results and the required payload/response shapes.

### Type consistency

All layers use `lecture_id` for the fixed catalogue identifier. `bundle_id` remains the telemetry/asset compatibility alias and equals `lecture_id` for every generated or seeded lecture. The shared API returns `lecture_id`; Admin posts form field `lecture_id`; learner links and asset routes use that same value.

## Execution Handoff

Plan complete and saved to `C:\Su\VinLab\Hackathon\codebase\docs\superpowers\plans\2026-09-18-shared-five-lecture-catalog.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?