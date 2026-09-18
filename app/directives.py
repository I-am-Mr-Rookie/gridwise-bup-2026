import math
from typing import Any

from app.schemas import OptimizeRequest


DIRECTIVE_TYPES = {
    "solar_reduction",
    "minimum_battery_reserve",
    "no_charge_window",
    "no_discharge_window",
    "max_grid_window",
    "no_op",
}


class InvalidDirectiveError(ValueError):
    pass


def validate_directives(raw: Any, request: OptimizeRequest) -> list[dict[str, Any]]:
    if not isinstance(raw, dict) or set(raw) != {"interpretations"}:
        raise InvalidDirectiveError("Invalid directive response object.")
    entries = raw["interpretations"]
    if not isinstance(entries, list) or len(entries) != len(request.operator_notes):
        raise InvalidDirectiveError("Every operator note must have one interpretation.")

    validated = []
    for expected_index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != {
            "note_index", "applies", "directive_type", "structured_adjustment", "explanation"
        }:
            raise InvalidDirectiveError("Invalid directive entry shape.")
        if entry["note_index"] != expected_index or type(entry["note_index"]) is not int:
            raise InvalidDirectiveError("Directive entries must be in note_index order.")
        kind = entry["directive_type"]
        if not isinstance(kind, str) or kind not in DIRECTIVE_TYPES or type(entry["applies"]) is not bool:
            raise InvalidDirectiveError("Invalid directive type or applies value.")
        if not isinstance(entry["explanation"], str) or not entry["explanation"].strip():
            raise InvalidDirectiveError("Directive explanation must be non-empty.")

        adjustment = entry["structured_adjustment"]
        if kind == "no_op":
            if entry["applies"] or adjustment is not None:
                raise InvalidDirectiveError("no_op must be non-applicable with a null adjustment.")
            normalized = None
        else:
            if not entry["applies"] or not isinstance(adjustment, dict):
                raise InvalidDirectiveError("Applicable directives require an adjustment.")
            normalized = _validate_adjustment(kind, adjustment, request)

        validated.append(
            {
                "note_index": expected_index,
                "applies": entry["applies"],
                "directive_type": kind,
                "structured_adjustment": normalized,
                "explanation": entry["explanation"].strip(),
            }
        )
    return validated


def _validate_adjustment(kind: str, adjustment: dict[str, Any], request: OptimizeRequest) -> dict[str, Any]:
    allowed = {"hours", "factor", "minimum_energy_kwh", "max_grid_kwh"}
    if set(adjustment) != allowed:
        raise InvalidDirectiveError("Invalid structured_adjustment shape.")
    hours = adjustment["hours"]
    if (
        not isinstance(hours, list)
        or not hours
        or any(type(hour) is not int or not 0 <= hour <= 23 for hour in hours)
        or hours != sorted(set(hours))
    ):
        raise InvalidDirectiveError("Directive hours must be unique sorted integers from 0 through 23.")

    values = {name: adjustment[name] for name in allowed - {"hours"}}
    required = {
        "solar_reduction": "factor",
        "minimum_battery_reserve": "minimum_energy_kwh",
        "max_grid_window": "max_grid_kwh",
    }.get(kind)
    if any(value is not None for name, value in values.items() if name != required):
        raise InvalidDirectiveError("Directive contains unsupported adjustment values.")
    if required is None:
        return {"hours": hours}

    value = values[required]
    if type(value) not in {int, float}:
        raise InvalidDirectiveError("Directive adjustment must be a finite number.")
    try:
        value = float(value)
    except OverflowError as exc:
        raise InvalidDirectiveError("Directive adjustment must be a finite number.") from exc
    if not math.isfinite(value):
        raise InvalidDirectiveError("Directive adjustment must be a finite number.")
    if required == "factor" and not 0 <= value <= 1:
        raise InvalidDirectiveError("Solar factor must be between 0 and 1.")
    if required != "factor" and value < 0:
        raise InvalidDirectiveError("Directive adjustment must be non-negative.")
    if required == "minimum_energy_kwh" and value > request.battery.capacity_kwh:
        raise InvalidDirectiveError("Battery reserve cannot exceed capacity.")
    return {"hours": hours, required: value}
