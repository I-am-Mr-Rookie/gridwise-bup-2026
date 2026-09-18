import math
from typing import Any

from app.schemas import OptimizeRequest


def check_plan(
    request: OptimizeRequest,
    directives: list[dict[str, Any]],
    response: dict[str, Any],
    tolerance: float = 1e-6,
) -> list[str]:
    errors: list[str] = []
    source = {item.hour: item for item in request.hours}
    plan = response.get("hourly_plan", [])
    if len(plan) != 24 or {item.get("hour") for item in plan} != set(range(24)):
        return ["hourly_plan must contain exactly one entry for every hour 0 through 23"]

    solar_cap = {hour: source[hour].solar_kwh for hour in range(24)}
    reserve = {hour: request.battery.minimum_energy_kwh for hour in range(24)}
    no_charge: set[int] = set()
    no_discharge: set[int] = set()
    grid_cap = {hour: math.inf for hour in range(24)}
    for directive in directives:
        if not directive.get("applies", True) or directive["directive_type"] == "no_op":
            continue
        kind = directive["directive_type"]
        adjustment = directive["structured_adjustment"]
        affected = adjustment["hours"]
        if kind == "solar_reduction":
            for hour in affected:
                solar_cap[hour] = min(solar_cap[hour], source[hour].solar_kwh * adjustment["factor"])
        elif kind == "minimum_battery_reserve":
            for hour in affected:
                reserve[hour] = max(reserve[hour], adjustment["minimum_energy_kwh"])
        elif kind == "no_charge_window":
            no_charge.update(affected)
        elif kind == "no_discharge_window":
            no_discharge.update(affected)
        elif kind == "max_grid_window":
            for hour in affected:
                grid_cap[hour] = min(grid_cap[hour], adjustment["max_grid_kwh"])
        else:
            errors.append(f"unsupported directive type: {kind}")

    ordered = sorted(plan, key=lambda item: item["hour"])
    previous_energy = request.battery.initial_energy_kwh
    for item in ordered:
        hour = item["hour"]
        values = [item.get(name) for name in ("grid_kwh", "solar_used_kwh", "battery_kwh", "battery_energy_after_kwh")]
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value < -tolerance for value in values):
            errors.append(f"hour {hour}: numeric values must be finite and non-negative")
            continue
        grid, solar, amount, energy = values
        action = item.get("battery_action")
        if action not in {"charge", "discharge", "idle"}:
            errors.append(f"hour {hour}: invalid battery_action")
            continue
        charge = amount if action == "charge" else 0
        discharge = amount if action == "discharge" else 0
        if action == "idle" and abs(amount) > tolerance:
            errors.append(f"hour {hour}: idle battery_kwh must be zero")
        expected_energy = previous_energy + charge - discharge
        if abs(energy - expected_energy) > tolerance:
            errors.append(f"hour {hour}: invalid battery transition")
        if energy < reserve[hour] - tolerance or energy > request.battery.capacity_kwh + tolerance:
            errors.append(f"hour {hour}: battery energy outside bounds")
        if charge > request.battery.max_charge_kwh_per_hour + tolerance or discharge > request.battery.max_discharge_kwh_per_hour + tolerance:
            errors.append(f"hour {hour}: battery rate exceeded")
        if hour in no_charge and charge > tolerance:
            errors.append(f"hour {hour}: no-charge directive violated")
        if hour in no_discharge and discharge > tolerance:
            errors.append(f"hour {hour}: no-discharge directive violated")
        if solar > solar_cap[hour] + tolerance:
            errors.append(f"hour {hour}: effective solar exceeded")
        if grid > grid_cap[hour] + tolerance:
            errors.append(f"hour {hour}: grid cap exceeded")
        balance = grid + solar + discharge - source[hour].demand_kwh - charge
        if abs(balance) > tolerance:
            errors.append(f"hour {hour}: energy balance violated")
        previous_energy = energy

    if abs(previous_energy - request.battery.initial_energy_kwh) > tolerance:
        errors.append("final battery energy must equal initial battery energy")
    calculated_grid = sum(item["grid_kwh"] for item in ordered)
    calculated_cost = sum(item["grid_kwh"] * source[item["hour"]].tariff_bdt_per_kwh for item in ordered)
    calculated_peak = max(item["grid_kwh"] for item in ordered)
    for name, calculated in (("total_grid_kwh", calculated_grid), ("total_cost_bdt", calculated_cost), ("peak_grid_kwh", calculated_peak)):
        if not isinstance(response.get(name), (int, float)) or abs(response[name] - calculated) > tolerance:
            errors.append(f"{name} does not match hourly_plan")
    return errors


def assert_valid_plan(request: OptimizeRequest, directives: list[dict[str, Any]], response: dict[str, Any]) -> None:
    errors = check_plan(request, directives, response)
    if errors:
        raise AssertionError("; ".join(errors))

