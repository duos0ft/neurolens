from typing import Literal

from pydantic import BaseModel, ConfigDict


class EmployeePreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    directness: Literal["low", "balanced", "high"]
    response_length: Literal["short", "medium", "detailed"]
    highlight_ambiguity: bool
    step_by_step_guidance: bool
    always_show_next_step: bool


class UpdateEmployeePreferencesRequest(BaseModel):
    directness: Literal["low", "balanced", "high"] | None = None
    response_length: Literal["short", "medium", "detailed"] | None = None
    highlight_ambiguity: bool | None = None
    step_by_step_guidance: bool | None = None
    always_show_next_step: bool | None = None
