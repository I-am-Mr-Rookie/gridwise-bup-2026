# GridWise live-deployed HTTP evidence

- Timestamp: `2026-09-18T23:16:24+06:00`
- Server: `externally managed Uvicorn`
- Runner: `.\.venv\Scripts\python.exe tests\run_http_samples.py --base-url https://gridwise-production-1034.up.railway.app --output RUN8_LIVE_RESULTS.md`
- Expected runtime configuration: `gpt-5.6-luna`, effort `high`, label `live-deployed` (verify remote configuration separately)
- Result: `14/14` requests passed; public acceptance `10/10`
- Latency: cold `3256 ms`; warm n=`13`, p50 `2818 ms`, p95 `4141 ms` (nearest-rank)

| Case | Phase | Interpretation | Replay | Cost | Latency ms | Exception |
|---|---|---:|---:|---:|---:|---|
| SAMPLE-01 | cold | PASS | PASS | PASS | 3256 | - |
| SAMPLE-01 | warm-public | PASS | PASS | PASS | 2895 | - |
| SAMPLE-02 | warm-public | PASS | PASS | PASS | 2818 | - |
| SAMPLE-03 | warm-public | PASS | PASS | PASS | 2475 | - |
| SAMPLE-04 | warm-public | PASS | PASS | PASS | 2471 | - |
| SAMPLE-05 | warm-public | PASS | PASS | PASS | 2407 | - |
| SAMPLE-06 | warm-public | PASS | PASS | PASS | 3908 | - |
| SAMPLE-07 | warm-public | PASS | PASS | PASS | 2735 | - |
| SAMPLE-08 | warm-public | PASS | PASS | PASS | 2698 | - |
| SAMPLE-09 | warm-public | PASS | PASS | PASS | 3503 | - |
| SAMPLE-10 | warm-public | PASS | PASS | PASS | 3173 | - |
| TARGET-PARAPHRASE | warm-targeted | PASS | PASS | PASS | 3726 | - |
| TARGET-DISTRACTOR | warm-targeted | PASS | PASS | PASS | 1951 | - |
| TARGET-COMBINATION | warm-targeted | PASS | PASS | PASS | 4141 | - |
