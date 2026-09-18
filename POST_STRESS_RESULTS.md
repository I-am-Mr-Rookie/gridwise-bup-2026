# Post-stress closure evidence

Recorded on 2026-09-18. No credential value is stored here.

## Isolated clean-source real-provider replay

- Timestamp: `2026-09-18T17:40:42.987634+00:00`.
- Environment: independently installed `gridwise-stress-fresh/clean-repro` virtual environment.
- Runtime: `gpt-5.6-luna`, reasoning effort `high`, one real provider call, no mocked interpreter.
- SAMPLE-01: HTTP 200; exact scenario echo and expected interpretation; independent schedule replay passed; 38,365 BDT reference cost matched; 3,765.655 ms.
- Sanitized source evidence: `gridwise-stress-fresh/CLEAN_LIVE_RESULTS.json` in the parent workspace.

## Pullable fallback image

- Image: `ghcr.io/i-am-mr-rookie/gridwise-bup-2026@sha256:9e4334347d97af868f2d9100ca56cb88a3d903bd4f3b765865e9e0372bb98f89`.
- Source commit: `ddd3b69b8f5039e5157834e80e9ce496f971769a`.
- [GitHub Actions publication run](https://github.com/I-am-Mr-Rookie/gridwise-bup-2026/actions/runs/35376376249): success.
- Anonymous GHCR manifest request: HTTP 200; returned digest exactly matched the reference above.
- Build-context safety: probable literal-secret scan found no matches; `.env*`, Git metadata, virtual environments, caches, tests, Markdown evidence, and logs are excluded; the Dockerfile copies only `requirements.txt` and `app/`.
- Independent remote pull/start: Railway service `gridwise-fallback-verify`, deployment `e2de9ce2-fdcd-43e1-8f59-0fe6bb33da08`, status `SUCCESS`, health check passed.
- Digest-pinned SAMPLE-01: HTTP 200; expected interpretation, independent replay, and 38,365 BDT cost all passed in 2,757.561 ms using one provider call.
- Sanitized source evidence: `gridwise-stress-fresh/FALLBACK_LIVE_RESULTS.json` in the parent workspace.

Local Docker was not used. The fallback proof is the anonymous registry fetch plus Railway pulling and running the exact digest.
