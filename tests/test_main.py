import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app


client = TestClient(app, raise_server_exceptions=False)


def valid_request() -> dict:
    return {
        "scenario_id": "RUN-1",
        "operator_notes": ["Keep the usual schedule."],
        "hours": [
            {"hour": hour, "demand_kwh": 1, "solar_kwh": 0, "tariff_bdt_per_kwh": 1}
            for hour in range(24)
        ],
        "battery": {
            "capacity_kwh": 10,
            "initial_energy_kwh": 5,
            "minimum_energy_kwh": 2,
            "max_charge_kwh_per_hour": 2,
            "max_discharge_kwh_per_hour": 2,
        },
    }


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_requests_are_400() -> None:
    assert client.post("/optimize-energy", content="{").status_code == 400
    request = valid_request()
    request["hours"].pop()
    assert client.post("/optimize-energy", json=request).status_code == 400

    for request in (
        {**valid_request(), "operator_notes": []},
        {**valid_request(), "operator_notes": ["a", "b", "c", "d"]},
        {**valid_request(), "hours": [{**valid_request()["hours"][0], "demand_kwh": "bad"}] + valid_request()["hours"][1:]},
        {**valid_request(), "hours": [{**valid_request()["hours"][0], "tariff_bdt_per_kwh": -1}] + valid_request()["hours"][1:]},
    ):
        assert client.post("/optimize-energy", json=request).status_code == 400


@pytest.mark.parametrize("number", ["1e309", "-1e309", "NaN", "Infinity"])
def test_nonfinite_input_returns_safe_400(number) -> None:
    request = valid_request()
    request["hours"][0]["demand_kwh"] = "NONFINITE_SENTINEL"
    request["operator_notes"] = ["PRIVATE_INPUT_SENTINEL"]
    body = json.dumps(request).replace('"NONFINITE_SENTINEL"', number)
    response = client.post("/optimize-energy", content=body, headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert response.json()["detail"]
    assert "PRIVATE_INPUT_SENTINEL" not in response.text
    assert all(set(error) == {"loc", "msg", "type"} for error in response.json()["detail"])


def test_valid_request_runs_full_pipeline(monkeypatch) -> None:
    calls = 0

    async def fake_interpret(request) -> list[dict]:
        nonlocal calls
        calls += 1
        return [{
            "note_index": 0,
            "applies": False,
            "directive_type": "no_op",
            "structured_adjustment": None,
            "explanation": "No scheduling change.",
        }]

    monkeypatch.setattr(main, "interpret_directives", fake_interpret)
    response = client.post("/optimize-energy", json=valid_request())
    assert response.status_code == 200
    assert response.json()["scenario_id"] == "RUN-1"
    assert response.json()["directive_interpretation"][0]["directive_type"] == "no_op"
    assert calls == 1


def test_provider_failure_is_controlled_and_redacted(monkeypatch) -> None:
    async def fail(_):
        raise main.LLMError("PRIVATE_PROVIDER_SENTINEL")

    monkeypatch.setattr(main, "interpret_directives", fail)
    response = client.post("/optimize-energy", json=valid_request())
    assert response.status_code == 500
    assert response.json() == {"detail": "LLM directive interpretation failed safely."}
    assert "PRIVATE_PROVIDER_SENTINEL" not in response.text
