# Code Review Fixes

Scope: the whole repository. That covers the FastAPI app (`app/`), the tests, the Dockerfile, `.dockerignore`/`.gitignore`, `.env.example`, the GitHub workflow, and the docs. The project is a GridWise energy-scheduling API: an LLM turns operator notes into structured directives, local guardrails validate them, a SciPy/HiGHS LP optimizes the schedule, and an independent checker replays the result.

Overall the code is in good shape. It has strict input validation, redacted errors, guardrailed LLM output, an independent replay checker, and a randomized DP cross-check of the solver. No secrets are committed: `.env.example` has an empty key, and `.env` is ignored by Git and excluded from Docker builds.

## Issues found and fixed

| Severity | Issue | Fix |
|---|---|---|
| Medium | `solver.solve` raised `InfeasibleScheduleError` (HTTP 422) on **any** `milp` failure, including iteration/time limits and numerical errors. That reported a server-side fault to the client as "no feasible schedule". | 422 is now raised only for HiGHS status 2 (infeasible). Every other failure raises `RuntimeError`, which `main.py` already maps to the redacted 500. I checked the 100 randomized DP cases: infeasible instances always return status 2. |
| Medium | No length limit on `operator_notes` or `scenario_id`. On a public endpoint, an arbitrarily large note was forwarded to the paid LLM provider (cost/abuse risk) and then failed late with a 500. | `NonEmptyText` now has `max_length=2000`, so oversized text gets a 400 before any provider call. Organizer notes are about 200 characters. |
| Low | `llm.interpret_directives` did not catch `UnicodeDecodeError` from an undecodable provider body. It still became a 500, but through the generic "Optimization failed safely" path instead of the LLM-failure path. | The `except` now catches `ValueError`. That covers `JSONDecodeError`, `UnicodeDecodeError` and `InvalidDirectiveError`, and the now-unused import is removed. |
| Low | The container ran as root. | The Dockerfile adds `USER nobody`. The app writes nothing to disk, and bytecode writing is already disabled. |
| Low | The README's local-request step writes `sample-01-request.json` into the repo root, and that file was not ignored. | `.gitignore` now has `sample-*-request.json`. |
| Low (docs) | README inaccuracies: it still said "No commits, pushes, or deployment before Run 8" although Run 8 is done; it said to run commands "from this `gridwise` directory" (the repo is `gridwise-bup-2026`); and it did not mention the new note limit, the 422-vs-500 split, or the non-root user. | All of these lines are corrected. |

Regression tests added in `tests/test_hardening.py`: oversized note returns 400; a non-infeasible optimizer failure is not reported as infeasible; an undecodable provider body raises `LLMError`. All three fail on the original code and pass on the fixed code.

## Deliberately not fixed

- **`pytest` is in `requirements.txt`, so it ships in the production image.** Harmless. Splitting into dev/prod requirements would change the documented install commands.
- **`actions/checkout@v4` is not pinned to a commit SHA, and the default `persist-credentials` is on.** The workflow runs only on manual `workflow_dispatch`, so the risk is low. Pinning is a policy choice for the owner.
- **The fallback image digest in the README was built from the earlier Dockerfile (running as root).** I left the documented, verified digest unchanged. A new image would need the gated publish workflow.
- **Process logs** (`STATUS.md`, `RUN*_*.md`, `POST_STRESS_RESULTS.md`, `MODEL_PREFERENCE.md`) are left as written. They are historical evidence, not instructions.
- **The README links to parent-directory planning files** that are not in the repo. The README already says they are workspace-only references.
- **`StarletteDeprecationWarning` (install `httpx2`) during tests** comes from a dependency. It does not affect the build.

## Build/test results

- `python -m pytest -q -p no:cacheprovider`, run in a fresh venv built from the pinned `requirements.txt` (Python 3.12.3; the project targets 3.11): **156 passed**, 1 dependency deprecation warning. Before the changes: 153 passed.
- `git diff --check`: clean.
- I did not build or run the Docker image, per the repo's no-local-Docker rule, so the `USER nobody` change is unverified in a container. I made no live provider calls.
