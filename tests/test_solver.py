import json
from pathlib import Path
from time import perf_counter

from app.checker import assert_valid_plan
from app.schemas import OptimizeRequest
from app.solver import solve


CASES = Path(__file__).parents[2] / "BUP_CSE_FEST_2026_Participant_Docs" / "BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json"


def test_sample_01_solver_and_checker() -> None:
    case = json.loads(CASES.read_text(encoding="utf-8-sig"))["cases"][0]
    request = OptimizeRequest.model_validate(case["input"])
    directives = [
        {"directive_type": "solar_reduction", "structured_adjustment": {"hours": [12, 13], "factor": 0.25}},
        {"directive_type": "no_op", "structured_adjustment": None, "applies": False},
    ]

    solve(request, directives)  # warm HiGHS before timing
    started = perf_counter()
    response = solve(request, directives)
    elapsed = perf_counter() - started

    assert_valid_plan(request, directives, response)
    naive_all_grid_cost = sum(item.demand_kwh * item.tariff_bdt_per_kwh for item in request.hours)
    assert response["total_cost_bdt"] < naive_all_grid_cost
    assert abs(response["total_cost_bdt"] - case["expected_output"]["total_cost_bdt"]) <= 0.01
    assert elapsed < 0.1
