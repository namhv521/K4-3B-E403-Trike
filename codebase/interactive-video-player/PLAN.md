# Interactive Recap Video Player Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the website with a fullscreen desktop recap-video player that handles checkpoint input, branching, scoring, and logs.

**Architecture:** A dependency-free state engine controls learning behavior. A pygame/OpenCV adapter renders video and overlays while pygame mixer plays generated narration. JSONL logging and a small entry point keep the runtime testable and packageable.

**Tech Stack:** Python 3.10+, pygame, OpenCV, unittest, PyInstaller, PowerShell

**Spec:** `codebase/interactive-video-player/DESIGN.md`

## Global Constraints

- The lesson content is recap education, not game content.
- No browser, HTTP server, HTML, CSS, or JavaScript runtime.
- Correct answers seek forward exactly ten seconds.
- Wrong answers show explanation for exactly five seconds.
- First-attempt score cannot be restored; later attempts remain logged.
- Runtime logs must not contain API keys or full source content.

---

### Task 1: Deterministic learning engine

**Files:**
- Create: `codebase/interactive-video-player/engine.py`
- Create: `codebase/interactive-video-player/tests/test_engine.py`

**Interfaces:**
- Produces: `Session(lesson, session_id, now)`, `open_checkpoint()`,
  `submit_answer()`, `choose_recovery()`, and `summary()`.

- [ ] Write tests for first-attempt scoring, ten-second seek, five-second
  recovery lock, `0/1` branching, later-attempt logging, and misconceptions.
- [ ] Run `python -m unittest tests/test_engine.py -v` and verify missing-module failure.
- [ ] Implement immutable-style state transitions with plain dict events.
- [ ] Run the test and verify all engine cases pass.

### Task 2: Fullscreen media runtime

**Files:**
- Create: `codebase/interactive-video-player/player.py`
- Create: `codebase/interactive-video-player/tests/test_player.py`
- Create: `codebase/interactive-video-player/logger.py`
- Create: `codebase/interactive-video-player/tests/test_logger.py`

**Interfaces:**
- Consumes: engine session methods and lesson assets.
- Produces: `PlaybackClock`, `InteractivePlayer.run()`, and
  `append_event(log_dir, event)`.

- [ ] Write clock tests for play, pause, seek, and elapsed-time calculation.
- [ ] Write logger tests for JSONL append and secret-field removal.
- [ ] Run both tests and verify missing implementation failures.
- [ ] Implement the clock and JSONL logger using only the standard library.
- [ ] Implement pygame/OpenCV rendering, audio control, keyboard dispatch,
  question/feedback overlays, countdown, and final report.
- [ ] Run the tests and `python -m py_compile player.py logger.py`.

### Task 3: Application, assets, and packaging

**Files:**
- Create: `codebase/interactive-video-player/main.py`
- Create: `codebase/interactive-video-player/requirements.txt`
- Create: `codebase/interactive-video-player/build.ps1`
- Create: `codebase/interactive-video-player/README.md`
- Replace: `codebase/interactive-video-player/assets/*`
- Remove: prior website HTML, CSS, JavaScript, and HTTP server files.

**Interfaces:**
- Consumes: `assets/lesson.json`, `assets/recap.mp4`, and
  `assets/narration.mp3`.
- Produces: `python main.py [--windowed]` and `dist/interactive-recap.exe`.

- [ ] Add startup validation tests for missing and malformed assets.
- [ ] Implement `main.py` with absolute asset paths relative to the executable.
- [ ] Copy the regenerated narrated bundle from `video-generator/output`.
- [ ] Document installation, controls, running, log location, and EXE build.
- [ ] Run a windowed smoke test through one correct and one wrong checkpoint.

### Task 4: Generator long-record hardening and final verification

**Files:**
- Modify: `codebase/video-generator/generate_content.py`
- Modify: `codebase/video-generator/tests/test_generate_content.py`

**Interfaces:**
- Produces: bounded digest inputs even when one transcript or text record is
  larger than the configured batch budget.

- [ ] Add a failing test with one record larger than `batch_chars` and assert
  every digest request remains within the budget.
- [ ] Split oversized record text into locator-preserving chunks.
- [ ] Run generator and player test suites.
- [ ] Verify narrated MP4 streams with `ffprobe` and non-silence with FFmpeg
  `volumedetect`.
- [ ] Review the exact staged paths, commit only both `codebase` modules, push
  `namhv521`, and verify the remote SHA.
