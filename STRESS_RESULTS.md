# Strict local stress audit - 2026-09-18

153 offline tests passed (two existing dependency deprecation warnings).

- All ten organizer public solver/reference-cost cases.
- 100 seeded small integer battery instances checked against an independent dynamic-programming oracle, including infeasible cases, zero tariffs/rates/capacity, overlaps, and solar curtailment.
- Eight concurrent offline ASGI requests passed independent schedule replay; health remained available.
- Adversarial regressions: NaN aggregates, malformed plans, strict JSON numeric types, exact scenario-ID echo, extreme/unhashable model values, provider total deadline, and event-loop responsiveness.
- Fresh Python 3.11.15 environment installed all 25 resolved packages from the cache and passed the same 153 tests plus actual Uvicorn health/start/stop. Dotenv loading was explicitly disabled during clean-copy verification; no provider credentials or parent configuration were required.
- 23 candidate Git files scanned against three configured protected values: zero leaks. Organizer fixture SHA-256 unchanged. `git diff --check` passed.

## Repairs

Finite/type/shape checks in the independent checker; strict request numbers; preserve scenario-ID whitespace for exact echo; normalized directive-validation errors; 20-second total provider deadline; threadpool solver execution; official controlled-error HTTP 500 instead of 502; safe `.env.*` Git exclusions; absolute-only numeric tolerance and correct remote labeling in the HTTP evidence runner.

No model/provider or solver formulation change. No new dependency. No local Docker execution. Tests mock the provider and do not establish live LLM interpretation or deployment readiness. Historical live-local evidence remains in RUN4_RESULTS.md. Run 8 deployed evidence, pullable fallback image, and video playback sign-off remain separate gates.

Full local round log and pre-audit rollback snapshot are outside the repository in `../gridwise-stress-audit-2026-09-18/`; they are not required to run the application.
