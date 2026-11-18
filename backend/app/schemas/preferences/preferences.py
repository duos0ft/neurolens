from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, field_validator


class EmployeePreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    directness: Literal["low", "balanced", "high"]
    response_length: Literal["short", "medium", "detailed"]
    highlight_ambiguity: bool
    step_by_step_guidance: bool
    always_show_next_step: bool

    timezone: str | None
    effective_timezone: str


class UpdateEmployeePreferencesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    directness: Literal["low", "balanced", "high"] | None = None
    response_length: Literal["short", "medium", "detailed"] | None = None
    highlight_ambiguity: bool | None = None
    step_by_step_guidance: bool | None = None
    always_show_next_step: bool | None = None

    timezone: str | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        timezone = value.strip()

        try:
            ZoneInfo(timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError("Invalid IANA timezone") from error

        return timezone
