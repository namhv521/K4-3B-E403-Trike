# Interactive Recap Video Player Design

## Goal

Replace the browser website with a fullscreen Windows learning-video player.
The content remains a 60–90 second recap lesson; only the interaction model is
game-like. The learner sees the video, questions, feedback, and final score in
one uninterrupted fullscreen experience.

## Deliverable

The agent bundle contains `recap.mp4`, `narration.mp3`, and `lesson.json`. The
desktop player consumes that bundle and can be run from Python or packaged as
`interactive-recap.exe`. A normal MP4 remains non-interactive; the executable
is the runtime that receives keys, branches playback, and writes logs.

## Learning flow

1. The recap video and narration play fullscreen.
2. At a checkpoint the frame freezes and four answers appear over the video.
3. `A`–`D` submits an answer. Every submission is logged.
4. A correct answer completes the checkpoint, seeks forward ten seconds, and
   unlocks playback through the next checkpoint.
5. A wrong answer permanently loses that checkpoint's first-attempt point and
   shows the explanation for exactly five seconds.
6. After the explanation, `0` restarts from the beginning and `1` skips to the
   next checkpoint. Returning later can produce additional logged attempts but
   cannot restore the first-attempt score.
7. The final frame shows score, attempt count, corrected-after-review count,
   and recurring misconceptions.

## Architecture

- `engine.py`: deterministic state transitions, scoring, recovery, and event
  creation. It has no GUI or media dependencies.
- `player.py`: pygame/OpenCV fullscreen rendering, narration playback,
  keyboard input, checkpoint overlays, and time synchronization.
- `logger.py`: append-only UTF-8 JSONL event storage.
- `main.py`: loads and validates assets, constructs the engine/player, and
  starts the application.
- `assets/`: generated lesson bundle copied from `video-generator/output`.
- `build.ps1`: PyInstaller command for a Windows executable.

## Media synchronization

OpenCV decodes `recap.mp4`; pygame mixer plays `narration.mp3`. A monotonic
clock is the playback authority. Pause stores the exact lesson time. Seek sets
both the OpenCV position and audio start position, then resets the clock
anchor. This keeps checkpoint decisions independent from frame rate.

## Controls

- `Space`: play or pause outside a checkpoint.
- `A`, `B`, `C`, `D`: answer the visible question.
- `0`, `1`: recovery command after the five-second explanation.
- `R`: restart after completion.
- `Esc`: exit safely.

## Logging

Events are written to `runtime-logs/YYYY-MM-DD.jsonl`. Allowed event data
includes session, timestamp, playback time, checkpoint, attempt number,
selected answer, correctness, response time, misconception, recovery action,
and score. API keys and source contents are never logged.

## Constraints

- Windows-first prototype; Python 3.10 or newer.
- No browser, HTTP server, or HTML/CSS/JavaScript runtime.
- Fullscreen by default with a windowed flag for development and tests.
- Offline playback after the lesson bundle has been generated.
- Existing user source files and unrelated repository changes stay untouched.
