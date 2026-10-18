# Frontend notes

## What existed before

No frontend. The repo was an API-only FastAPI service (`app/main.py`) with `GET /health` and
`POST /optimize-energy`, no templates, no static assets and no JS toolchain.

## What was added

- `app/static/index.html`: a single-file operator console (inline CSS and JS, no build step,
  no dependencies, no external fonts or CDNs). It:
  - shows API health in the header (from `GET /health`);
  - has a JSON request editor prefilled with the public SAMPLE-01 input, plus "Load JSON file" and
    "Reset to sample";
  - posts to `POST /optimize-energy` and renders total grid energy, cost and peak import, the plan
    summary, one card per directive interpretation (type, explanation, structured adjustment),
    and a 24-row hourly table with an inline grid-import bar and color-coded battery actions;
  - reports invalid JSON on the client, lists 400 validation errors by field, and shows 422/500
    details;
  - builds all output with `textContent` only, so operator notes and LLM explanations cannot
    inject HTML;
  - is accessible: labelled controls, visible focus rings, an `aria-live` result region, a
    `role="alert"` status line, a scrollable table region you can reach by keyboard, row/column
    header scopes, and color that is never the only signal (actions are also written as text);
  - is responsive: two columns at 1000px and wider, one column below that. The table scrolls
    inside its own box, so the page itself never scrolls sideways at 375px.
- `app/main.py`: a new `GET /` route (left out of the OpenAPI schema) that returns the page with
  `FileResponse`. The page calls the API with relative URLs from the same origin, so no CORS
  setup is needed. The existing endpoints are unchanged.
- `tests/test_main.py`: `test_console_page_is_served` checks that `/` returns the HTML page.

The page lives under `app/` because the `Dockerfile` copies only `app/`, so the console ships
with the existing image and needs no Dockerfile changes.

## How to run

Start the API as described in `README.md`, then open the root URL:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# open http://127.0.0.1:8000/
```

Clicking **Optimize** makes a real LLM call, so `MERGE_API_KEY` must be set; without it you get
the redacted 500 message. The health check and input validation work without a key.

## Verification performed

- `pytest -q`: 157 passed (includes the new test).
- Headless Chromium against a local server with the LLM call replaced by SAMPLE-01's expected
  directives: 24 rows rendered, totals 2,692.5 kWh and 38,365 BDT; no page-level horizontal
  overflow at 1366px or 375px; the invalid-JSON and 400 error paths display correctly; no JS errors.
