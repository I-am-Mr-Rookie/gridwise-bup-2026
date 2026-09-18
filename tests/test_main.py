from fastapi.testclient import TestClient

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


def test_valid_request_reaches_controlled_stub() -> None:
    response = client.post("/optimize-energy", json=valid_request())
    assert response.status_code == 500
    assert response.json() == {"detail": "Optimization is not available until solver integration."}
