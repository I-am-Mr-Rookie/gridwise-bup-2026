from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


NonNegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Hour(StrictModel):
    hour: int = Field(ge=0, le=23)
    demand_kwh: NonNegative
    solar_kwh: NonNegative
    tariff_bdt_per_kwh: NonNegative


class Battery(StrictModel):
    capacity_kwh: NonNegative
    initial_energy_kwh: NonNegative
    minimum_energy_kwh: NonNegative
    max_charge_kwh_per_hour: NonNegative
    max_discharge_kwh_per_hour: NonNegative

    @model_validator(mode="after")
    def validate_energy_bounds(self) -> "Battery":
        if self.minimum_energy_kwh > self.initial_energy_kwh:
            raise ValueError("minimum_energy_kwh cannot exceed initial_energy_kwh")
        if self.initial_energy_kwh > self.capacity_kwh:
            raise ValueError("initial_energy_kwh cannot exceed capacity_kwh")
        return self


class OptimizeRequest(StrictModel):
    scenario_id: NonEmptyText
    operator_notes: list[NonEmptyText] = Field(min_length=1, max_length=3)
    hours: list[Hour] = Field(min_length=24, max_length=24)
    battery: Battery

    @model_validator(mode="after")
    def validate_hours(self) -> "OptimizeRequest":
        if {entry.hour for entry in self.hours} != set(range(24)):
            raise ValueError("hours must contain each integer from 0 through 23 exactly once")
        return self

