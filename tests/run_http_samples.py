"""Run the public and targeted Run 4 cases against a live local HTTP server."""

import argparse
import json
import math
import os
import sys
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
from time import perf_counter, sleep
from urllib.parse import urlparse

import httpx
import uvicorn

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from app.checker import assert_valid_plan
from app.schemas import OptimizeRequest
from app.solver import solve


CASES = ROOT / "tests" / "data" / "BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json"


def directives_match(actual: list[dict], expected: list[dict]) -> bool:
    if len(actual) != len(expected):
        return False
    for got, want in zip(actual, expected):
        if any(got.get(key) != want.get(key) for key in ("note_index", "applies", "directive_type")):
            return False
        got_adjustment, want_adjustment = got.get("structured_adjustment"), want.get("structured_adjustment")
        if got_adjustment is None or want_adjustment is None:
            if got_adjustment is not want_adjustment:
                return False
            continue
        if set(got_adjustment) != set(want_adjustment):
            return False
        for key, value in want_adjustment.items():
            candidate = got_adjustment[key]
            if key == "hours":
                if candidate != value:
                    return False
            elif type(candidate) not in {int, float} or not math.isfinite(candidate) or not math.isclose(candidate, value, rel_tol=0, abs_tol=0.01):
                return False
    return True


def targeted_cases(base: dict) -> list[dict]:
    cases = []
    for case_id, notes, directives in (
        (
            "TARGET-PARAPHRASE",
            ["Between 1 PM and 3 PM today, the battery must not take any charge."],
            [{"note_index": 0, "applies": True, "directive_type": "no_charge_window", "structured_adjustment": {"hours": [13, 14]}, "explanation": "ignored"}],
        ),
        (
            "TARGET-DISTRACTOR",
            ["Tomorrow's pricing meeting starts at 3 PM; do not alter today's energy schedule."],
            [{"note_index": 0, "applies": False, "directive_type": "no_op", "structured_adjustment": None, "explanation": "ignored"}],
        ),
        (
            "TARGET-COMBINATION",
            ["From 5 PM until 7 PM today, keep at least 80 kWh in the battery.", "Do not discharge the battery from 10 AM until noon today."],
            [
                {"note_index": 0, "applies": True, "directive_type": "minimum_battery_reserve", "structured_adjustment": {"hours": [17, 18], "minimum_energy_kwh": 80}, "explanation": "ignored"},
                {"note_index": 1, "applies": True, "directive_type": "no_discharge_window", "structured_adjustment": {"hours": [10, 11]}, "explanation": "ignored"},
            ],
        ),
    ):
        request = deepcopy(base["input"])
        request["scenario_id"] = case_id
        request["operator_notes"] = notes
        model = OptimizeRequest.model_validate(request)
        reference = solve(model, directives)
        cases.append({"id": case_id, "input": request, "expected_output": {"directive_interpretation": directives, "total_cost_bdt": reference["total_cost_bdt"]}})
    return cases


def run_case(client: httpx.Client, case: dict, phase: str) -> dict:
    started = perf_counter()
    try:
        response = client.post("/optimize-energy", json=case["input"])
        latency_ms = (perf_counter() - started) * 1000
        response.raise_for_status()
        result = response.json()
        expected = case["expected_output"]
        interpretation_ok = directives_match(result.get("directive_interpretation", []), expected["directive_interpretation"])
        assert_valid_plan(OptimizeRequest.model_validate(case["input"]), expected["directive_interpretation"], result)
        replay_ok = True
        cost_ok = math.isclose(result["total_cost_bdt"], expected["total_cost_bdt"], rel_tol=0, abs_tol=0.01)
        error = "" if interpretation_ok and cost_ok else "interpretation mismatch" if not interpretation_ok else "cost differs from reference"
    except Exception as exc:
        latency_ms = (perf_counter() - started) * 1000
        interpretation_ok = replay_ok = cost_ok = False
        error = f"{type(exc).__name__}: {str(exc)[:120]}".replace("|", "/").replace("\n", " ")
    return {
        "case": case["id"], "phase": phase, "interpretation": interpretation_ok,
        "replay": replay_ok, "cost": cost_ok, "latency_ms": latency_ms, "error": error,
    }


def nearest_rank(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


@contextmanager
def local_server(enabled: bool, base_url: str):
    if not enabled:
        yield
        return
    parsed = urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"} or not parsed.port:
        raise ValueError("--start-server requires a local HTTP base URL with an explicit port")
    server = uvicorn.Server(uvicorn.Config("app.main:app", host=parsed.hostname, port=parsed.port, log_level="warning", access_log=False))
    thread = Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        if not thread.is_alive():
            raise RuntimeError("Local Uvicorn server failed to start")
        sleep(0.05)
    else:
        raise TimeoutError("Local Uvicorn server did not become ready")
    try:
        yield
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        if thread.is_alive():
            raise RuntimeError("Local Uvicorn server did not stop")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, default=ROOT / "RUN4_RESULTS.md")
    parser.add_argument("--start-server", action="store_true", help="start and stop local Uvicorn in this process")
    parser.add_argument("--health-only", action="store_true", help="verify server lifecycle without provider calls")
    args = parser.parse_args()

    public = json.loads(CASES.read_text(encoding="utf-8-sig"))["cases"]
    command = f".\\.venv\\Scripts\\python.exe tests\\run_http_samples.py --base-url {args.base_url} --output {args.output.name}"
    if args.start_server:
        command += " --start-server"
    rows = []
    with local_server(args.start_server, args.base_url):
        with httpx.Client(base_url=args.base_url, timeout=30) as client:
            health = client.get("/health")
            health.raise_for_status()
            if health.json().get("status") != "ok":
                raise RuntimeError("Health response did not report ready")
            if args.health_only:
                print("Local server lifecycle: PASS")
                return 0
            rows.append(run_case(client, public[0], "cold"))
            rows.extend(run_case(client, case, "warm-public") for case in public)
            rows.extend(run_case(client, case, "warm-targeted") for case in targeted_cases(public[0]))

    warm = [row["latency_ms"] for row in rows if row["phase"] != "cold"]
    passed = sum(all(row[key] for key in ("interpretation", "replay", "cost")) for row in rows)
    label = "live-local" if urlparse(args.base_url).hostname in {"127.0.0.1", "localhost"} else "live-deployed"
    lines = [
        f"# GridWise {label} HTTP evidence", "",
        f"- Timestamp: `{datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}`",
        f"- Server: `{'in-process Uvicorn via --start-server' if args.start_server else 'externally managed Uvicorn'}`",
        f"- Runner: `{command}`",
        f"- Expected runtime configuration: `{os.getenv('LLM_MODEL', 'gpt-5.6-luna')}`, effort `{os.getenv('LLM_REASONING_EFFORT', 'high')}`, label `{label}` (verify remote configuration separately)",
        f"- Result: `{passed}/{len(rows)}` requests passed; public acceptance `{sum(all(r[k] for k in ('interpretation', 'replay', 'cost')) for r in rows if r['phase'] == 'warm-public')}/10`",
        f"- Latency: cold `{rows[0]['latency_ms']:.0f} ms`; warm n=`{len(warm)}`, p50 `{nearest_rank(warm, 0.50):.0f} ms`, p95 `{nearest_rank(warm, 0.95):.0f} ms` (nearest-rank)",
        "", "| Case | Phase | Interpretation | Replay | Cost | Latency ms | Exception |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(f"| {row['case']} | {row['phase']} | {'PASS' if row['interpretation'] else 'FAIL'} | {'PASS' if row['replay'] else 'FAIL'} | {'PASS' if row['cost'] else 'FAIL'} | {row['latency_ms']:.0f} | {row['error'] or '-'} |")
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{label}: {passed}/{len(rows)} requests passed; evidence: {args.output}")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
