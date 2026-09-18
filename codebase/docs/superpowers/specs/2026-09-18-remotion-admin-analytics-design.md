# Remotion Admin and Learning Analytics Design

## Capability

VLearn gains a local two-role prototype: an admin selects an authorised lesson
folder in a browser, starts a grounded recap-generation job, reviews the
generated Remotion bundle and anonymous learning analytics; a learner opens a
published bundle and uses the existing checkpoint player, live logs and result
screen.

## Fixed constraints

- `lesson.json` remains the versioned source of truth for scenes, citations,
  checkpoint timecodes, answers and misconceptions.
- The Python generator remains responsible for source extraction, OpenRouter
  grounding, lesson validation and Edge TTS. The new renderer consumes a
  validated lesson; it must not invent lesson content.
- Remotion replaces the visual renderer only. Its reusable patterns are a
  generic Composition, `Series` scene sequencing, audio-derived scene timing,
  subtle transitions and chunked subtitles. Branding/content from the external
  Docker example is not copied.
- Admin upload accepts only supported source extensions and writes a per-job
  staging directory below the local runtime root. OpenRouter credentials stay
  in server environment variables and are never sent to the browser or logs.
- Event ingestion and dashboard aggregation use the telemetry allowlist. No
  user name, source text, prompt, key, cookie or full free-text answer is
  persisted.
- The console is explicitly local-development only. Role pages demonstrate
  workflow but are not production authentication or authorization.
- This is a learning-recap prototype, not a classroom LMS, official gradebook,
  public ranking, long-term learner profile or general tutor.

## Actors and surfaces

| Actor | Surface | Outcome |
| --- | --- | --- |
| Admin | `/admin` | Upload course files, supply a recap prompt, create a job, inspect its bundle and aggregate analytics. |
| Learner | `/learn/<bundle-id>` | Watch one generated recap, answer checkpoints, see live local log and final metrics. |
| Local service | `/api/*` | Owns job staging, generator subprocesses, bundle publication and allowlisted telemetry aggregation. |

## State and flow

```text
admin folder selection
  -> validated upload staging
  -> job queued/running
  -> Python grounding + Edge TTS
  -> Remotion Composition render
  -> immutable bundle publication
  -> learner session events
  -> server allowlist validation
  -> aggregate by bundle/checkpoint/misconception
  -> admin dashboard
```

Job states are `queued`, `running`, `succeeded`, and `failed`. A failed job
stores only a redacted diagnostic. A bundle is published only when the lesson,
sources and rendered MP4 exist and duration validation succeeds.

## Interfaces

- `POST /api/admin/jobs`: multipart files plus a short recap prompt; responds
  with `{id,status}`.
- `GET /api/admin/jobs/<id>`: current job status and public bundle metadata;
  no source text or secret trace.
- `GET /api/admin/analytics?bundle_id=<id>`: views, completed sessions,
  checkpoint accuracy, repeated misconception counts, average response time
  and fast-completion count.
- `POST /api/events`: one allowlisted event plus server-assigned received time;
  accepts only a published `bundle_id` and schema-valid body.
- `GET /api/bundles/<id>/lesson.json`, `sources.json`, `recap.mp4`: learner
  bundle assets.

## Data layout

```text
interactive-website/runtime/
  jobs/<job-id>/input/          # temporary authorised upload; gitignored
  jobs/<job-id>/status.json     # redacted state
  bundles/<bundle-id>/          # recap.mp4, lesson.json, sources.json, metadata
  telemetry/events.jsonl        # allowlisted anonymous events
```

The server deletes failed staging input after a configurable local retention
window; the prototype defaults to removing it when a job finishes. Published
bundle source catalogs remain minimal and do not contain original source text.

## Rendering contract

`video-generator` writes a generic Remotion input file from validated scenes.
The Remotion project renders 1280×720, 30fps MP4 with each scene in a `Series`.
Narration is segmented by scene, rendered by Edge TTS, and its measured media
duration determines scene frames. The renderer returns the actual duration;
the Python publisher validates this against `lesson.duration_seconds` before
publishing.

## User-visible metrics

The learner result keeps score, first-attempt accuracy, attempts, mean response
time, actual completion time and fast-view warning. The admin dashboard shows
only aggregated counts: sessions/views, completion, time-to-complete, each
checkpoint's first-attempt accuracy and recurring misconceptions. It labels
fixture/mock data honestly.

## Non-goals

- Production login, identity, consent workflow, retention policy enforcement
  for real learners, cloud object storage or multi-host job queues.
- Automatic changes to teaching material based on analytics. The dashboard
  recommends review targets; an admin still decides what recap to generate.
- Copying the external Remotion template's Docker-specific scenes or brand.

## Acceptance criteria

1. Admin can select a folder in the browser, submit a job and see unambiguous
   `queued/running/succeeded/failed` progress without using a CLI.
2. A successful job produces a grounded, schema-valid bundle rendered by the
   internal Remotion project and opens it in the existing interactive learner
   flow.
3. User events reach the local API only through the allowlist and dashboard
   identifies the checkpoint and misconception most often incorrect.
4. The learner view still pauses on checkpoint timecode, shows answers and
   final result/live logs.
5. Tests cover upload extension rejection, event redaction, aggregation,
   job-status validation, Remotion render-command contract and web core.
