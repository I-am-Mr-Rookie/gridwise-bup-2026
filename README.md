# GridWise

Minimal Python 3.11 implementation for the BUP CSE Fest 2026 online preliminary.

## Read first

- Current progress and exact next step: [STATUS.md](STATUS.md)
- Runtime model preference and verification: [MODEL_PREFERENCE.md](MODEL_PREFERENCE.md)
- No commits, pushes, or deployment **before Run 8**. Local Docker on this device is intentionally out of scope and must not be run or troubleshot. In Run 8, use Docker only in Railway through the authenticated Railway Codex integration. Preserve current uncommitted work; registry publication, visibility changes, and contest submission remain separately gated.
- Build runbook: [../GPT-5.6-Sol-GridWise-Runbook.html](../GPT-5.6-Sol-GridWise-Runbook.html)
- Canonical problem statement: [../BUP_CSE_FEST_2026_Participant_Docs/BUP_CSE_FEST_2026_Preliminary_Problem_Statement_GridWise_LLM.pdf](../BUP_CSE_FEST_2026_Participant_Docs/BUP_CSE_FEST_2026_Preliminary_Problem_Statement_GridWise_LLM.pdf)
- Repository-local public cases: [tests/data/BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json](tests/data/BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json), an unchanged organizer-provided copy. SHA-256: `FA6ABD71868E0FAF429A87429D7D4A2B7BFD38C5551565637498D7FEC68D5F32`.
- Parent-directory links above are workspace planning references, not runtime/test dependencies. Run commands below from this `gridwise` directory.

## API and architecture

- `GET /health` returns `{"status":"ok"}`.
- `POST /optimize-energy` accepts a scenario ID, 1-3 operator notes, all 24 hourly demand/solar/tariff rows, and battery limits.
- Malformed input returns 400, infeasible constraints 422, and provider/interpretation or unexpected failures a redacted 500, matching the problem's response-code contract.

```text
request -> Pydantic validation -> one structured-output LLM call
        -> local directive guardrails -> SciPy/HiGHS optimization
        -> independent schedule replay -> response
```

The response contains one ordered interpretation per note, a 24-row hourly plan, total grid energy, total cost, peak grid import, and a summary. Supported actions are solar reduction, minimum battery reserve, no-charge, no-discharge, and maximum-grid windows; irrelevant notes become `no_op`. Time windows are half-open: 1 PM to 3 PM means hours 13 and 14.

## Environment

| Variable | Required | Purpose/default |
|---|---:|---|
| `MERGE_API_KEY` | yes | Merge gateway credential; no default |
| `MERGE_BASE_URL` | no | `https://api-gateway.merge.dev/v1/openai` |
| `LLM_MODEL` | no | `gpt-5.6-luna` |
| `LLM_REASONING_EFFORT` | no | `high` |

Copy `.env.example` to `.env` and set the key locally. `.env` is ignored by Git and excluded from the Railway build context. Never print, commit, record, or place credentials in request files.

## Clean local reproduction (PowerShell, non-Docker)

Prerequisites: [`uv`](https://docs.astral.sh/uv/) and network access for Python/dependency installation. Run from this repository root:

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
# Set MERGE_API_KEY locally; never overwrite an existing .env.
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The 24 offline tests do not require a provider key or make model calls. They replay all 10 public cases using organizer-expected directives, not an LLM interpretation.

In another PowerShell window:

```powershell
curl.exe --fail-with-body http://127.0.0.1:8000/health

# Extract the exact organizer SAMPLE-01 input; do not hand-edit 24 hourly rows.
@'
import json
from pathlib import Path
data = json.loads(Path("tests/data/BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json").read_text(encoding="utf-8"))
Path("sample-01-request.json").write_text(json.dumps(data["cases"][0]["input"]), encoding="utf-8")
'@ | .\.venv\Scripts\python.exe -

curl.exe --fail-with-body `
  -H "Content-Type: application/json" `
  --data-binary "@sample-01-request.json" `
  http://127.0.0.1:8000/optimize-energy
```

For a managed live-local run over every organizer case:

```powershell
.\.venv\Scripts\python.exe tests\run_http_samples.py --start-server
```

The runner owns Uvicorn startup, readiness, and shutdown. It requires a valid provider key and makes quota-dependent calls.

## Example request and response

The extraction command above writes the exact valid SAMPLE-01 request. Its important fields are:

```json
{
  "scenario_id": "SAMPLE-01",
  "operator_notes": [
    "Facilities will wash the rooftop solar panels from noon until 2 PM. During cleaning, usable solar should be treated as roughly 25% of the forecast.",
    "The sports office moved next month's registration deadline."
  ],
  "hours": "24 organizer-provided hourly objects in the extracted file",
  "battery": {
    "capacity_kwh": 220,
    "initial_energy_kwh": 110,
    "minimum_energy_kwh": 40,
    "max_charge_kwh_per_hour": 50,
    "max_discharge_kwh_per_hour": 50
  }
}
```

Expected semantics and aggregates (the complete 24-row reference is `cases[0].expected_output` in the sample pack):

```json
{
  "scenario_id": "SAMPLE-01",
  "directive_interpretation": [
    {
      "note_index": 0,
      "applies": true,
      "directive_type": "solar_reduction",
      "structured_adjustment": {"hours": [12, 13], "factor": 0.25}
    },
    {
      "note_index": 1,
      "applies": false,
      "directive_type": "no_op",
      "structured_adjustment": null
    }
  ],
  "hourly_plan": "24 validated rows",
  "total_grid_kwh": 2692.5,
  "total_cost_bdt": 38365,
  "peak_grid_kwh": 175
}
```

Equivalent optimal schedules and explanation wording may differ; directive semantics, replay validity, and cost tolerance still apply.

## Previously verified gateway details (Runs 1-3)

- Base URL: `https://api-gateway.merge.dev/v1/openai`
- Runtime choice: `gpt-5.6-luna`, effort `high`
- Strict structured output works. Every object in `response_format` must set `additionalProperties: false`; `uniqueItems` is rejected and must be enforced locally.
- Never commit `.env` or print the API key.

## Current code map

- `app/schemas.py`: strict request validation.
- `app/solver.py`: 24-hour SciPy/HiGHS cost optimizer with all five actionable directive constraints.
- `app/checker.py`: independent replay of schedule invariants and totals.
- `app/llm.py`: one-call Merge structured-output client and production interpretation prompt.
- `app/directives.py`: deterministic LLM-output guardrails and normalization.
- `app/main.py`: health endpoint and full interpretation -> guardrails -> solver -> checker pipeline.
- `tests/`: API/guardrail checks and all 10 organizer-ground-truth solver replays, with repository-local samples.
- `.dockerignore`: excludes local environment secrets, Git metadata, virtualenv, and caches from future image builds; image contents and container behavior must be verified in Run 8, not before.
- `Dockerfile`: minimal Python 3.11 container startup with `0.0.0.0` binding and shell-expanded `${PORT:-8000}`; not built or run yet.

## Dependencies and credits

- FastAPI and Pydantic: HTTP API and strict validation.
- Uvicorn: ASGI server.
- SciPy `milp` with HiGHS and all variables continuous: linear optimization (no integer constraints).
- HTTPX: async Merge gateway request.
- python-dotenv: ignored local environment loading.
- pytest: offline verification.
- uv: reproducible Python 3.11 environment and dependency installation.
- Merge gateway and `gpt-5.6-luna`: natural-language directive interpretation.
- Organizer-provided GridWise public sample pack: local fixtures and expected semantics.

Exact pinned versions are in `requirements.txt`.

## Evidence and limitations

- [RUN4_RESULTS.md](RUN4_RESULTS.md) contains prior live-local all-10 evidence; it is not a deployed SLA or proof of current provider availability.
- [RUN5_PACKAGING.md](RUN5_PACKAGING.md) contains draft Railway/container commands; they are unverified.
- Public examples do not prove hidden-case performance. Local guardrails reject malformed or invented model output.
- Provider outage, invalid credentials, exhausted quota, or the 20-second total provider deadline produces a safe 500. Solver work runs off the API event loop so health remains responsive.
- The continuous one-hour model assumes no battery efficiency loss, following the supplied challenge.
- No deployment, Railway build, pullable image, or container-runtime evidence exists yet.

## Docker, Railway, and video boundaries

Do not use Docker on this device. During Run 8, Docker is only for Railway's remote build/deployment path via the authenticated Railway Codex integration. The prepared Dockerfile remains unverified until Railway builds and runs it; registry publication still needs separate authorization.

This README supplies the later <=3-minute video with the factual architecture, demo commands, SAMPLE-01 semantics, evidence, and limitations. Run 7 may create the script/storyboard, capture local visuals/API output, synthesize authorized ElevenLabs narration, and assemble/verify captions, audio, and video with FFmpeg. Keep `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` only in an ignored local environment; never print, embed, record, or commit them. Run 6 does not record, synthesize, assemble, publish, upload, or submit video.
