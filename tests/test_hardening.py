"""Offline adversarial regressions; never contact a model provider."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import random
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app import llm, main
from app.checker import check_plan
from app.directives import InvalidDirectiveError, validate_directives
from app.schemas import OptimizeRequest
from app.solver import solve
from app.solver import InfeasibleScheduleError


CASES = json.loads((Path(__file__).parent / "data" / "BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json").read_text(encoding="utf-8-sig"))["cases"]


def sample():
    case = deepcopy(CASES[0])
    return OptimizeRequest.model_validate(case["input"]), case["expected_output"]["directive_interpretation"]


@pytest.mark.parametrize("field", ["total_grid_kwh", "total_cost_bdt", "peak_grid_kwh"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True])
def test_checker_rejects_invalid_aggregates(field, value):
    request, directives = sample()
    response = solve(request, directives)
    response[field] = value
    assert check_plan(request, directives, response)


@pytest.mark.parametrize("mutation", ["null_plan", "null_entry", "string_grid", "missing_grid", "bool_hour", "list_action"])
def test_checker_handles_malformed_plan_without_crashing(mutation):
    request, directives = sample()
    response = solve(request, directives)
    if mutation == "null_plan":
        response["hourly_plan"] = None
    elif mutation == "null_entry":
        response["hourly_plan"][0] = None
    elif mutation == "string_grid":
        response["hourly_plan"][0]["grid_kwh"] = "bad"
    elif mutation == "missing_grid":
        del response["hourly_plan"][0]["grid_kwh"]
    elif mutation == "bool_hour":
        response["hourly_plan"][0]["hour"] = False
    else:
        response["hourly_plan"][0]["battery_action"] = []
    assert check_plan(request, directives, response)


@pytest.mark.parametrize("field,value", [("hour", True), ("hour", "0"), ("demand_kwh", True), ("solar_kwh", "0"), ("tariff_bdt_per_kwh", False)])
def test_numeric_schema_rejects_non_json_numbers(monkeypatch, field, value):
    request, directives = sample()
    async def fake(_):
        return directives
    monkeypatch.setattr(main, "interpret_directives", fake)
    body = request.model_dump()
    body["hours"][0][field] = value
    with TestClient(main.app, raise_server_exceptions=False) as client:
        assert client.post("/optimize-energy", json=body).status_code == 400


def test_provider_has_total_deadline(monkeypatch):
    request, _ = sample()
    monkeypatch.setenv("MERGE_API_KEY", "offline-test-key")
    monkeypatch.setattr(llm, "LLM_TIMEOUT_SECONDS", 0.02, raising=False)
    class SlowClient:
        def __init__(self, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def post(self, *args, **kwargs):
            # Models a slow stream whose per-read timeout never fires.
            await asyncio.sleep(0.15)
            raise httpx.ReadTimeout("offline sentinel")
    monkeypatch.setattr(llm.httpx, "AsyncClient", SlowClient)
    async def run():
        started = time.perf_counter()
        with pytest.raises(llm.LLMError):
            await llm.interpret_directives(request)
        assert time.perf_counter() - started < 0.10
    asyncio.run(run())


def test_optimizer_does_not_block_event_loop(monkeypatch):
    request, directives = sample()
    result = solve(request, directives)
    async def fake(_):
        return directives
    def slow_solve(*args):
        time.sleep(0.15)
        return deepcopy(result)
    monkeypatch.setattr(main, "interpret_directives", fake)
    monkeypatch.setattr(main, "solve", slow_solve)
    async def run():
        started = time.perf_counter()
        task = asyncio.create_task(main.optimize_energy(request))
        await asyncio.sleep(0.02)
        assert time.perf_counter() - started < 0.10
        await task
    asyncio.run(run())


@pytest.mark.parametrize("kind,value", [("max_grid_window", 10**1000), ([], 1)], ids=["overflow", "unhashable-type"])
def test_guardrail_converts_malformed_values_to_validation_error(kind, value):
    request, _ = sample()
    request.operator_notes = ["Synthetic note."]
    raw = {"interpretations": [{"note_index": 0, "applies": True, "directive_type": kind,
        "structured_adjustment": {"hours": [0], "factor": None, "minimum_energy_kwh": None, "max_grid_kwh": value},
        "explanation": "Synthetic."}]}
    with pytest.raises(InvalidDirectiveError):
        validate_directives(raw, request)


def test_scenario_id_echo_is_exact(monkeypatch):
    request, directives = sample()
    async def fake(_):
        return directives
    monkeypatch.setattr(main, "interpret_directives", fake)
    body = request.model_dump()
    body["scenario_id"] = "  exact-id  "
    with TestClient(main.app) as client:
        response = client.post("/optimize-energy", json=body)
        assert response.status_code == 200
        assert response.json()["scenario_id"] == body["scenario_id"]


@pytest.mark.parametrize("seed", range(100))
def test_random_solver_against_independent_integer_dp(seed):
    """Integer instances have integral LP optima; DP uses no solver/checker internals."""
    rng = random.Random(seed)
    capacity = rng.randint(0, 6)
    initial = rng.randint(0, capacity)
    base = rng.randint(0, initial)
    rate_in, rate_out = rng.randint(0, 4), rng.randint(0, 4)
    hours = [{"hour": h, "demand_kwh": rng.randint(0, 9), "solar_kwh": 2*rng.randint(0, 5),
              "tariff_bdt_per_kwh": rng.randint(0, 9)} for h in range(24)]
    solar = [h["solar_kwh"] for h in hours]
    reserve, incoming, outgoing, grid_cap = [base]*24, [rate_in]*24, [rate_out]*24, [float("inf")]*24
    directives = []
    kinds = ["solar_reduction", "minimum_battery_reserve", "no_charge_window", "no_discharge_window", "max_grid_window"]
    for index in range(3):
        kind = rng.choice(kinds)
        affected = sorted(rng.sample(range(24), rng.randint(1, 12)))
        adjustment = {"hours": affected}
        if kind == "solar_reduction":
            value = rng.choice([0, 0.5, 1])
            adjustment["factor"] = value
            for h in affected:
                solar[h] = min(solar[h], hours[h]["solar_kwh"]*value)
        elif kind == "minimum_battery_reserve":
            value = rng.randint(0, capacity)
            adjustment["minimum_energy_kwh"] = value
            for h in affected:
                reserve[h] = max(reserve[h], value)
        elif kind == "no_charge_window":
            for h in affected:
                incoming[h] = 0
        elif kind == "no_discharge_window":
            for h in affected:
                outgoing[h] = 0
        else:
            value = rng.randint(0, 10)
            adjustment["max_grid_kwh"] = value
            for h in affected:
                grid_cap[h] = min(grid_cap[h], value)
        directives.append({"note_index": index, "applies": True, "directive_type": kind,
                           "structured_adjustment": adjustment, "explanation": "Synthetic constraint."})
    request = OptimizeRequest.model_validate({"scenario_id": f"DP-{seed}", "operator_notes": ["Synthetic."]*3,
        "hours": hours, "battery": {"capacity_kwh": capacity, "initial_energy_kwh": initial,
        "minimum_energy_kwh": base, "max_charge_kwh_per_hour": rate_in, "max_discharge_kwh_per_hour": rate_out}})
    states = {initial: 0.0}
    for h in range(24):
        following = {}
        for before, cost in states.items():
            for after in range(reserve[h], capacity+1):
                delta = after-before
                net = hours[h]["demand_kwh"]+delta
                grid = max(0, net-solar[h])
                if -outgoing[h] <= delta <= incoming[h] and net >= 0 and grid <= grid_cap[h]:
                    candidate = cost+grid*hours[h]["tariff_bdt_per_kwh"]
                    following[after] = min(following.get(after, float("inf")), candidate)
        states = following
    if initial not in states:
        with pytest.raises(InfeasibleScheduleError):
            solve(request, directives)
    else:
        response = solve(request, directives)
        assert abs(response["total_cost_bdt"]-states[initial]) < 1e-6
        assert check_plan(request, directives, response) == []


def test_concurrent_offline_requests(monkeypatch):
    request, directives = sample()
    async def fake(_):
        await asyncio.sleep(0.001)
        return directives
    monkeypatch.setattr(main, "interpret_directives", fake)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://offline") as client:
            responses = await asyncio.gather(*(client.post("/optimize-energy", json=request.model_dump()) for _ in range(8)))
            assert all(r.status_code == 200 for r in responses)
            for response in responses:
                assert check_plan(request, directives, response.json()) == []
            assert (await client.get("/health")).json() == {"status": "ok"}
    asyncio.run(run())
