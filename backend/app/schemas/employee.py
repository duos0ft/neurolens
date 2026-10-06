from enum import StrEnum

from pydantic import BaseModel


class DirectnessLevel(StrEnum):
    LOW = "low"
    BALANCED = "balanced"
    HIGH = "high"


class ResponseLength(StrEnum):
    SHORT = "short"
    MEDIUM = "medium"
    DETAILED = "detailed"


class CommunicationPreferences(BaseModel):
    directness: DirectnessLevel = DirectnessLevel.BALANCED
    response_length: ResponseLength = ResponseLength.MEDIUM
    highlight_ambiguity: bool = True
    step_by_step_guidance: bool = True
    always_show_next_step: bool = True


class EmployeeProfile(BaseModel):
    display_name: str | None = None
    timezone: str = "UTC"
    preferences: CommunicationPreferences = CommunicationPreferences()
