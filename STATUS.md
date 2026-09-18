# GridWise Status

## Start here

- **Run 8 live deployment verified.** Public API: `https://gridwise-production-1034.up.railway.app`; public GitHub repository: `https://github.com/I-am-Mr-Rookie/gridwise-bup-2026`. The Railway production deployment built the repository Dockerfile remotely and is healthy. External runner passed 14/14 requests, including all 10 official public cases; warm p95 4,141 ms. Evidence: `RUN8_LIVE_RESULTS.md`.
- **Stress-test evaluation is deliberately separate from Run 8.** Do not continue the loop in this task. Use the workspace-root `GRIDWISE_STRESS_TEST_HANDOFF.md` in a fresh chat; apply any resulting patches with Ponytail's smallest-root-cause approach, then verify only affected behavior before a bounded live replay.
- Next: **Run 7 human playback sign-off**, not a rebuild. Caption-free `gridwise-solution-video-v03.mp4` passes technical checks; Koushik must watch the complete video before it is called presentation-ready. Then proceed to Run 8 only when requested. Read MODEL_PREFERENCE.md and the corrected parent runbook; preserve the current uncommitted changes.
- For local HTTP verification, run `.\.venv\Scripts\python.exe tests\run_http_samples.py --start-server`; it owns Uvicorn startup, readiness, and shutdown. Do not use hidden or compound PowerShell process wrappers.
- **No commits, pushes, or deployment before Run 8.** Latest instruction authorizes Railway deployment and commits/pushes of accumulated project work in Run 8. Do not run or troubleshoot Docker on this device; the remote Dockerfile build/deployment must use the authenticated Railway Codex integration. Ask only for missing destination/access details, not this authorization again. Registry publication, visibility changes, and contest submission remain separately gated; exclude secrets and unrelated files from commits.
- Event-date/window confirmation remains undocumented locally. This status records completed work, not proof of event compliance.

## Completed: Runs 1-5

- Local Git repository initialized on `main`; no remote configured. A local repository has no hosted private/public visibility setting.
- Python 3.11 FastAPI skeleton validates the official request shape.
- `GET /health` returned HTTP 200 with `{"status":"ok"}` under Uvicorn.
- Malformed and structurally invalid optimization requests return HTTP 400.
- Merge model: `gpt-5.6-luna`; reasoning effort: `high`.
- Strict JSON-schema SAMPLE-01 interpretation passed in 2,486 ms with the exact expected directive types and values.
- `solver.py` supports solar reduction, minimum reserve, no-charge, no-discharge, and maximum-grid constraints.
- `checker.py` independently replays hour coverage, numeric validity, battery transitions/bounds/rates, directives, solar, energy balance, end-of-day neutrality, and aggregates.
- SAMPLE-01 passed the checker at the exact reference cost: 38,365 BDT versus 54,515 BDT naïve all-grid.
- Warm SAMPLE-01 solve benchmark over 20 runs: 7.871 ms median, 11.544 ms p95, 14.550 ms maximum.
- Production prompt covers all six directive types, half-open time windows, factor semantics, distractors, and one entry per note.
- LLM output is locally guardrailed for exact note mapping, applies semantics, adjustment shape, sorted unique hours, finite values, and battery capacity.
- Each valid request makes one Merge call, then runs the existing solver and independent checker.
- Live HTTP SAMPLE-01: 200 in 3,721 ms; exact interpretation; exact 38,365 BDT reference cost.
- Live HTTP SAMPLE-02: 200 in 3,110 ms; exact interpretation; exact 42,885 BDT reference cost.
- Run 3 test result: 6 passed; superseded by the repair verification below.
- Run 1 commit: `ec95997`.
- Run 2 commit: `4d1b118`.
- Run 3 and subsequent repairs are intentionally uncommitted under the commit/push pause.

## Handoff repair - 2026-09-18

- Corrected stale entry documents, corrupted runbook formulas, inclusive solar factor range, reserve rejection, signed-delta LP description, and Runs 4-8 acceptance gates.
- Preserved application model/provider and solver. No live provider call was made during the audit/repair; prior HTTP timings above are historical, not current availability or p95 proof.
- Sanitized request-validation responses to avoid echoing raw input/context and to return JSON HTTP 400 for non-finite values; added regression coverage.
- Copied the unmodified organizer sample JSON into `tests/data/`; SHA-256 matches the original. All 10 ground-truth solver replays are now permanent tests. Added `.dockerignore`; no image has been built or verified.
- Repair verification: `python -m pytest -q -p no:cacheprovider` using the project virtualenv: **19 passed**, including all 10 ground-truth solver cases and four non-finite-input regressions. `git diff --check` passed (only line-ending notices). Do not claim Run 4 complete from offline tests.
- Isolated-source verification also passed **19 tests** without `.env` or the parent organizer folder; existing virtualenv dependencies were reused, so this is not a fresh dependency-install/container test. Runbook links resolve, corrupted text is removed, and all five entry documents carry the latest Run 8 deferral. No Docker command, provider call, deployment, commit, or push was performed during this repair.

## Run 4 - 2026-09-18

- Added one small live HTTP runner: `tests/run_http_samples.py`. Compact evidence: [RUN4_RESULTS.md](RUN4_RESULTS.md).
- Live-local `gpt-5.6-luna` with `high` effort passed **14/14** requests: one cold probe, all **10/10** organizer cases, and three targeted paraphrase/distractor/combined-directive cases.
- Every organizer case matched note order/index, applies, directive type, exact adjustment keys/hours, and numeric adjustments within 0.01. Returned plans passed independent replay against organizer-expected directives and stayed within 0.01 BDT of reference cost.
- End-to-end latency: cold **3,051 ms**; 13 warm requests had nearest-rank p50 **2,897 ms** and p95 **3,917 ms**. This is an initial local sample, not a deployed or broad reliability measurement.
- Focused request/provider safety checks cover malformed JSON, wrong hour/note counts, bad types, negative/non-finite input, malformed provider output, and redacted controlled 502 failure. Final local suite: **24 passed**; `git diff --check` passed with line-ending notices only.
- No Docker execution, deployment, commit, push, registry publication, visibility change, or contest submission occurred.

## Run 5 - 2026-09-18

- Added a minimal `python:3.11-slim` Dockerfile that installs the existing requirements, copies only `app/`, binds Uvicorn to `0.0.0.0`, and uses `sh -c` so `${PORT:-8000}` expands before `exec` replaces the shell.
- Hardened `.dockerignore` for all environment files, Git/Railway metadata, virtual environments, Python/test caches, tests, Markdown evidence, and logs.
- Prepared exact, explicitly unverified Run 8 Railway linking/variables/deployment/domain commands and a separately gated remote registry fallback in [RUN5_PACKAGING.md](RUN5_PACKAGING.md). A later instruction rules out local Docker execution on this device.
- Static packaging checks passed; the existing offline suite passed **24 tests** with two dependency deprecation warnings, `git diff --check` passed, and the new packaging files had zero secret-value scan matches. No Docker command, daemon troubleshooting, deployment, commit, push, registry publication, visibility change, or contest submission occurred.

## Run 6 - 2026-09-18

- Expanded README into a self-contained API/reproduction guide with architecture, exact environment/run/test/curl instructions, a repository-backed SAMPLE-01 example, dependency/tool credits, evidence, limitations, and explicit Railway/video boundaries.
- Reproduced from a new temporary directory containing only `app/`, `tests/`, `requirements.txt`, `.env.example`, and README: `uv` created a fresh Python 3.11.15 environment, installed 25 resolved packages, and the offline suite passed **24 tests** with two dependency deprecation warnings. The copy contained no `.git` or `.env` and had no parent-workspace dependency.
- The isolated Uvicorn `/health` check returned HTTP 200 with `{"status":"ok"}`. README sample extraction produced a valid 24-hour SAMPLE-01 request and matched the documented 38,365 BDT reference cost.
- README local links and required sections passed. Exact-value scanning checked 21 deliverable text files against the three locally configured Merge/ElevenLabs protected values and found no leak. `git diff --check` passed with line-ending notices only.
- Local Docker is explicitly prohibited on this device; Run 8 must use the authenticated Railway Codex integration for the remote Dockerfile build/deployment. No Docker, deployment, provider call, voice generation, video work, commit, push, registry publication, visibility change, or submission occurred in Run 6.

## Run 7 - local media technical gates passed, human playback pending (2026-09-18)

- Final-candidate local video: [caption-free v03](../GridWise%20Run%207%20Video/gridwise-solution-video-v03.mp4). Koushik's latest instruction removes burned-in captions; [editable SRT](../GridWise%20Run%207%20Video/captions-v02.srt) remains separate. No embedded subtitle stream. Detailed handoff: [RUN7_MEDIA.md](../GridWise%20Run%207%20Video/RUN7_MEDIA.md).
- Reused, unchanged: Astra `presentation.html` as the sole visual source, all seven canonical storyboard scenes, revised `narration.txt`/`narration.mp3`, and recorded SAMPLE-01 JSON. Preserved the original MP4, rejected contact sheet, original captions, source frames, and partial `build_video.py`. Original hashes are recorded in `preserved-assets-v03.json`.
- Verified existing narration through read-only ElevenLabs history: `eleven_multilingual_v2`, voice category `cloned`, exact narration-text match, and identical decoded PCM to the historical audio. MP3 container bytes differ; decoded audio does not. No narration regeneration, new dependency, audio upload, or application model/provider change.
- New work: deterministic 1920x1080 browser captures of all seven Astra scenes, cached local Whisper-small word timestamps, 32 canonical-text caption cues, final-only audio normalization, versioned encodes, seven-scene video contact sheet, and machine-readable QA/logs. Used installed Playwright, Pillow, faster-whisper, cached model, and FFmpeg only. No redesign or synthetic API/deployment footage.
- **v03 technical result:** 147.100 seconds; 1920x1080; 30 fps; H.264 High / yuv420p; AAC mono 48 kHz; x264 slow/stillimage CRF 14 and AAC 256 kb/s target. Final decoded audio: **-16.85 LUFS, -1.66 dBTP**. Full decode passed; valid `moov` precedes `mdat`; no silence gaps >=2 seconds at -45 dB. Size 6,884,879 bytes. SHA-256: `be68aea06549b4a1b5b2c6ec9d294eeba2ea22844993ff43d2e56e3dcf5b1458`.
- All seven HTML scenes passed browser geometry/font checks and visual review. Final-video contact sheet shows all seven without captions; sampled full-frame comparisons match their HTML captures. SAMPLE-01 saved response was independently replayed again and exactly matches `api-evidence.json`: HTTP statuses recorded as 200/200, 3,675 ms captured latency, 24 rows, solar factor 0.25 at hours 12/13, unrelated note `no_op`, PASS replay, 38,365 BDT. This continuation did not make a new optimization/provider request; HTTP timing remains the 22:02:11 capture, not a new measurement or SLA.
- **Idle suite: 24 passed, 2 existing dependency deprecation warnings in 5.93 seconds**, before capture/transcription/encoding. Prior SAMPLE-07 100.57 ms timing-only failure is treated as transient CPU-contention noise after this idle pass. No solver, timing threshold, functional assertion, or provider-path change. `git diff --check` passed with line-ending notices only.
- Secret-value scan found zero matches across Git-listed source/docs and media-workspace files, including HTML, captions, JSON, logs, raw media bytes, current speech ASR text, and audio/video metadata. Expected ignored `.env` carriers were excluded; no protected values printed. This is not exhaustive forensic OCR/ASR of every old fallback frame. Report: `verification-v03.json`.
- Run 8 read-only inventory refreshed: GitHub CLI authenticated with `repo` scope; local Git remote still absent, so exact GitHub repository destination is missing. Railway integration authenticated; one accessible project exists (`chic-fascination`), none named GridWise; target project/service/environment/domain remain unselected. Registry destination/tag/digest and publication authorization remain absent. No remote state changed.
- **Remaining gate:** full human playback of v03 for voice, pacing, scene synchronization, and readability; preview requested, not yet confirmed. Sidecar captions use ASR anchors with short documented interpolated spans and are not manually playback-approved. No deployed/container/external-judge evidence exists. Earlier captioned v02 is preserved but is not final: its decoded AAC peak was -1.48 dBTP, just above the gate; v03 uses 0.2 dB extra headroom and passes.
- No local Docker command, deployment, commit, push, visibility change, registry publication, upload, or contest submission occurred. Run 7 is **technically verified but not yet presentation-ready**; do not silently claim human sign-off.

## Remaining runs (corrected plan, not completed work)

| Run | Scope and exit gate |
|---|---|
| 6 | Self-contained README, dependency/tool credits, local non-Docker clean-directory reproduction, examples and test instructions. No deployment, commit, push, or Docker execution. |
| 7 | Final local hardening and handoff readiness; prepare/record the <=3-minute video, inventory Run 8 Git/Railway/registry access and exact destinations, check local evidence and secret safety. No external deployment or Docker execution. |
| 8 | Commit/push accumulated reviewed project work and deploy through the authenticated Railway Codex integration (authorized by latest instruction); let Railway remotely build/run the Dockerfile, then perform external all-10 HTTP checks, startup/latency checks, clean reproduction, and final package preflight. Never use local Docker on this device. Record a pullable exact image tag/digest only if separately authorized and remotely verified. Confirm video accessibility and submission details. Do not change repository visibility or submit the contest entry without authorization. |

## Run 8 - GitHub and Railway release (2026-09-18)

- Koushik explicitly authorized Run 8 and then explicitly authorized public GitHub visibility. Repository `I-am-Mr-Rookie/gridwise-bup-2026` is public. Commit `45813bc` contains the reviewed application, packaging, and hardening regressions; no configured protected values were found before push. The dedicated stress-test evaluation is deferred to a fresh chat and is not Run 8 evidence.
- Railway project `GridWise`, production service `gridwise`, and public domain were created through the authenticated integration. The existing local `MERGE_API_KEY` was transferred directly as a Railway secret without displaying or committing it; connector verification returned the variable name with values redacted. Runtime configuration remains Merge `gpt-5.6-luna`, effort `high`.
- Railway deployment `1f3c57d6-9997-46b4-8138-0706d1bc671d` succeeded after the secret was configured. `GET /health` returned HTTP 200 with `{"status":"ok"}`.
- External HTTPS verification passed 14/14: cold SAMPLE-01, all 10 public samples, paraphrase, distractor, and two-directive combination. Every response matched organizer-ground-truth interpretation, independent schedule replay, and reference cost. Cold 3,256 ms; warm p50 2,818 ms; warm p95 4,141 ms, within the rubric's full-credit <=5-second band. See `RUN8_LIVE_RESULTS.md`.
- The official JSON source and repository fixture remain semantically identical with 10 cases and identical local SHA-256 `FA6ABD71868E0FAF429A87429D7D4A2B7BFD38C5551565637498D7FEC68D5F32`.
- Docker remained stopped locally. Railway's remote Dockerfile build proves the deployed container path, but it is not a separately pullable registry fallback with an exact tag/digest. Registry publication remains unperformed because it was separately gated. Video human playback/accessibility and contest submission remain unverified/unperformed.
