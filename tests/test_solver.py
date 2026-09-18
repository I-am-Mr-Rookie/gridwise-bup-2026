import json
from pathlib import Path
from time import perf_counter

import pytest

from app.checker import assert_valid_plan
from app.schemas import OptimizeRequest
from app.solver import solve


CASES = Path(__file__).parent / "data" / "BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json"


@pytest.mark.parametrize("case", json.loads(CASES.read_text(encoding="utf-8-sig"))["cases"], ids=lambda case: case["id"])
def test_public_solver_and_checker(case) -> None:
    request = OptimizeRequest.model_validate(case["input"])
    # Organizer ground truth, not model-produced constraints. This is not an LLM test.
    directives = case["expected_output"]["directive_interpretation"]

    solve(request, directives)  # warm HiGHS before timing
    started = perf_counter()
    response = solve(request, directives)
    elapsed = perf_counter() - started

    assert_valid_plan(request, directives, response)
    naive_all_grid_cost = sum(item.demand_kwh * item.tariff_bdt_per_kwh for item in request.hours)
    assert response["total_cost_bdt"] <= naive_all_grid_cost + 0.01
    assert abs(response["total_cost_bdt"] - case["expected_output"]["total_cost_bdt"]) <= 0.01
    assert elapsed < 0.1
