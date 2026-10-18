# Deepening pass notes (second pass)

This pass builds on `REVIEW_FIXES.md` and does not repeat its fixes (HiGHS status split, note length limit, `UnicodeDecodeError`, non-root container, `.gitignore`, README corrections).

Superpowers skills used: `superpowers:test-driven-development` (every fix started from a failing test), `superpowers:systematic-debugging` (the false-infeasible bug was reproduced and its root cause confirmed before the fix), and `superpowers:verification-before-completion` (a fresh full-suite run backs every claim below).

## What I examined

- `app/solver.py`, `app/checker.py`, `app/directives.py`, `app/llm.py`, `app/main.py`, `app/schemas.py`, the Dockerfile, `.dockerignore`, `.env.example`, `tests/run_http_samples.py`, and the README.
- Solver/checker robustness under scaling. I scaled all 10 public cases (quantities and directive values together) by 1e-6 up to 1e20, and tariffs separately by up to 1e20. Results stay valid up to 1e16 for quantities and 1e15 for tariffs. They break at about 1e18, where values reach about 1e20.
- Extreme inputs through the HTTP endpoint (with the LLM stubbed): huge demand, tariff and capacity; a zero-size battery; tiny values; shuffled hour order; float hours; numeric strings.
- Error paths: the 422 contract over HTTP, a missing provider key, the provider success path, and logging on 500 responses.

## Fixes made

| Severity | Issue | Fix |
|---|---|---|
| Medium | HiGHS treats any magnitude of 1e20 or more as infinite. A feasible request with `demand_kwh = 1e20` (grid uncapped) got **422 "No feasible schedule exists."**, which is wrong. A tariff of 1e20 got a 500. A capacity of 1e20 was accepted. | `NonNegative` in `app/schemas.py` now has `le=1e12`, so such input gets a 400 at the trust boundary. 1e12 is far above any physical campus value and well inside the verified-stable range. |
| Medium | 500 responses were completely silent. `HTTPException(...) from exc` is not logged by FastAPI, so an operator could not tell a provider outage from a solver or checker fault. | `app/main.py` calls `logger.exception(...)` on both 500 branches. The client still gets only the redacted detail. I checked the real Uvicorn output: the traceback shows `LLMError: LLM service is not configured.` and no key or request content. |
| Low (docs) | The README's live-run command `run_http_samples.py --start-server` writes to the default `--output`, which is `RUN4_RESULTS.md`, so it overwrote the recorded Run 4 evidence. | The README command now passes `--output live-local-results.md` and explains why. |
| Low (docs) | The README did not mention the numeric input limit. | Documented in the API section. |

## Tests added (`tests/test_hardening.py`)

7 new test cases take the suite from 157 to **164**. They are all offline and make no provider calls.

- `test_out_of_range_magnitude_is_400_not_false_infeasible` (3 parametrized cases): RED before the fix (422, 500 and 200), GREEN after.
- `test_unexpected_failure_is_logged_but_redacted`: RED before the logging fix, GREEN after.
- `test_infeasible_directive_is_422_over_http`: covers the end-to-end 422 contract, which had only been tested at the solver level.
- `test_missing_provider_key_fails_without_network`: an unset key raises `LLMError` without any network call.
- `test_provider_success_is_parsed_and_guardrailed`: covers the LLM client's happy path, which had no test before. It checks the URL with the trailing slash stripped, the auth header, the strict `response_format`, the round-trip of the request JSON, and the normalized directives.

The last three passed on the first run because they cover existing behavior. To prove they catch regressions, I mutated the code temporarily (422 mapped to 500, `rstrip` removed, key check disabled). All three then failed, and I restored the code.

## Dependency updates (`requirements.txt`)

| Package | From | To | Result |
|---|---|---|---|
| fastapi | 0.141.1 | 0.143.3 | applied |
| uvicorn | 0.53.0 | 0.54.0 | applied |
| pydantic | 2.13.5 | 2.14.1 | applied (pydantic-core 2.50.1) |
| python-dotenv | 1.2.3 | 1.2.4 | applied |
| scipy | 1.17.1 | 1.18.1 | **not applied**: 1.18 requires Python >= 3.12, which would break the `python:3.11-slim` image. 1.17.1 is the newest 1.17.x. |
| httpx, pytest | — | — | already the latest |

I verified the updates in a fresh venv built from the updated `requirements.txt`: the full suite passed, and a real Uvicorn smoke test returned `/health` 200, `/` 200 HTML, a 400 for a malformed body, and a redacted 500 without a key. All four applied packages declare `Requires-Python >=3.10`.

## Intentionally left alone

- **A new `httpx.AsyncClient` per request**, which means a new TLS handshake each time. Reusing one client needs app lifespan management. The cost is small next to multi-second LLM latency (warm p95 is about 4.1 s).
- **The `StarletteDeprecationWarning` (install `httpx2`)** comes from FastAPI's `TestClient` import. It affects only tests.
- **No secondary objective in the LP.** When some hours have a zero tariff, ties can import grid energy that solar could have covered. These plans are still cost-optimal and pass the replay checker, and the organizer only scores cost.
- **Everything listed under "Deliberately not fixed" in `REVIEW_FIXES.md`** (pytest in prod requirements, unpinned `actions/checkout`, the fallback-image digest, process logs, parent-directory links).
- **The frontend (`app/static/index.html`)** was reviewed in the previous pass. I made no changes.

## Verification

- Python 3.12.3 (Python 3.11 is not installed on this machine, and `uv` is unavailable). No Docker, no live provider calls, no commits.
- Final run `python -m pytest -q -p no:cacheprovider` in a fresh venv from the updated `requirements.txt`: **164 passed**, 1 warning (the dependency deprecation above). Before this pass: 157 passed.
- The 7 new cases also pass on their own (7 passed). `git diff --check` is clean.
