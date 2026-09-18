from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from app.schemas import OptimizeRequest


class InfeasibleScheduleError(RuntimeError):
    pass


def _limits(request: OptimizeRequest, directives: list[dict[str, Any]]) -> tuple[np.ndarray, ...]:
    hours = sorted(request.hours, key=lambda item: item.hour)
    solar = np.array([item.solar_kwh for item in hours], dtype=float)
    reserve = np.full(24, request.battery.minimum_energy_kwh, dtype=float)
    charge = np.full(24, request.battery.max_charge_kwh_per_hour, dtype=float)
    discharge = np.full(24, request.battery.max_discharge_kwh_per_hour, dtype=float)
    grid_cap = np.full(24, np.inf, dtype=float)

    for directive in directives:
        if not directive.get("applies", True) or directive["directive_type"] == "no_op":
            continue
        kind = directive["directive_type"]
        adjustment = directive["structured_adjustment"]
        affected = adjustment["hours"]
        if kind == "solar_reduction":
            factor = adjustment["factor"]
            for hour in affected:
                solar[hour] = min(solar[hour], hours[hour].solar_kwh * factor)
        elif kind == "minimum_battery_reserve":
            reserve[affected] = np.maximum(reserve[affected], adjustment["minimum_energy_kwh"])
        elif kind == "no_charge_window":
            charge[affected] = 0
        elif kind == "no_discharge_window":
            discharge[affected] = 0
        elif kind == "max_grid_window":
            grid_cap[affected] = np.minimum(grid_cap[affected], adjustment["max_grid_kwh"])
        else:
            raise ValueError(f"Unsupported directive type: {kind}")
    return solar, reserve, charge, discharge, grid_cap


def solve(request: OptimizeRequest, directives: list[dict[str, Any]]) -> dict[str, Any]:
    hours = sorted(request.hours, key=lambda item: item.hour)
    solar_cap, reserve, charge_cap, discharge_cap, grid_cap = _limits(request, directives)
    n = 24
    grid, solar, battery_delta, energy = range(0, n), range(n, 2 * n), range(2 * n, 3 * n), range(3 * n, 4 * n)

    objective = np.zeros(4 * n)
    objective[list(grid)] = [item.tariff_bdt_per_kwh for item in hours]
    lower = np.zeros(4 * n)
    upper = np.full(4 * n, np.inf)
    upper[list(grid)] = grid_cap
    upper[list(solar)] = solar_cap
    lower[list(battery_delta)] = -discharge_cap
    upper[list(battery_delta)] = charge_cap
    lower[list(energy)] = reserve
    upper[list(energy)] = request.battery.capacity_kwh

    matrix = np.zeros((2 * n + 1, 4 * n))
    target = np.zeros(2 * n + 1)
    for hour in range(n):
        matrix[hour, grid[hour]] = 1
        matrix[hour, solar[hour]] = 1
        matrix[hour, battery_delta[hour]] = -1
        target[hour] = hours[hour].demand_kwh

        row = n + hour
        matrix[row, energy[hour]] = 1
        matrix[row, battery_delta[hour]] = -1
        if hour:
            matrix[row, energy[hour - 1]] = -1
        else:
            target[row] = request.battery.initial_energy_kwh
    matrix[-1, energy[-1]] = 1
    target[-1] = request.battery.initial_energy_kwh

    result = milp(
        objective,
        bounds=Bounds(lower, upper),
        constraints=LinearConstraint(matrix, target, target),
        options={"presolve": True},
    )
    if not result.success:
        raise InfeasibleScheduleError("No feasible schedule exists.")

    values = result.x

    def clean(value: float) -> float:
        return 0.0 if abs(value) < 1e-8 else round(float(value), 10)

    plan = []
    for hour in range(n):
        delta = clean(values[battery_delta[hour]])
        action = "charge" if delta > 0 else "discharge" if delta < 0 else "idle"
        plan.append(
            {
                "hour": hour,
                "grid_kwh": clean(values[grid[hour]]),
                "solar_used_kwh": clean(values[solar[hour]]),
                "battery_action": action,
                "battery_kwh": abs(delta),
                "battery_energy_after_kwh": clean(values[energy[hour]]),
            }
        )

    total_grid = sum(item["grid_kwh"] for item in plan)
    total_cost = sum(item["grid_kwh"] * hours[item["hour"]].tariff_bdt_per_kwh for item in plan)
    return {
        "scenario_id": request.scenario_id,
        "hourly_plan": plan,
        "total_grid_kwh": clean(total_grid),
        "total_cost_bdt": clean(total_cost),
        "peak_grid_kwh": clean(max(item["grid_kwh"] for item in plan)),
        "plan_summary": "Minimizes grid cost while satisfying battery, energy, and operator-directive constraints.",
    }

