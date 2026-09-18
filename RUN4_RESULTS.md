# Run 4 live-local HTTP evidence

- Timestamp: `2026-09-18T21:39:46+06:00`
- Server: `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Runner: `.\.venv\Scripts\python.exe tests\run_http_samples.py --base-url http://127.0.0.1:8000 --output RUN4_RESULTS.md`
- Runtime: `gpt-5.6-luna`, effort `high`, label `live-local`
- Result: `14/14` requests passed; public acceptance `10/10`
- Latency: cold `3051 ms`; warm n=`13`, p50 `2897 ms`, p95 `3917 ms` (nearest-rank)

| Case | Phase | Interpretation | Replay | Cost | Latency ms | Exception |
|---|---|---:|---:|---:|---:|---|
| SAMPLE-01 | cold | PASS | PASS | PASS | 3051 | - |
| SAMPLE-01 | warm-public | PASS | PASS | PASS | 3161 | - |
| SAMPLE-02 | warm-public | PASS | PASS | PASS | 2489 | - |
| SAMPLE-03 | warm-public | PASS | PASS | PASS | 2351 | - |
| SAMPLE-04 | warm-public | PASS | PASS | PASS | 2348 | - |
| SAMPLE-05 | warm-public | PASS | PASS | PASS | 2515 | - |
| SAMPLE-06 | warm-public | PASS | PASS | PASS | 3782 | - |
| SAMPLE-07 | warm-public | PASS | PASS | PASS | 3082 | - |
| SAMPLE-08 | warm-public | PASS | PASS | PASS | 2897 | - |
| SAMPLE-09 | warm-public | PASS | PASS | PASS | 3917 | - |
| SAMPLE-10 | warm-public | PASS | PASS | PASS | 3831 | - |
| TARGET-PARAPHRASE | warm-targeted | PASS | PASS | PASS | 2415 | - |
| TARGET-DISTRACTOR | warm-targeted | PASS | PASS | PASS | 1690 | - |
| TARGET-COMBINATION | warm-targeted | PASS | PASS | PASS | 3127 | - |
