from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApplicationSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_name: str
    default_timezone: str

    enable_task_assistance: bool
    enable_policy_assistance: bool
    enable_sentiment_analysis: bool


class UpdateApplicationSettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_name: str | None = Field(
        default=None,
        max_length=150,
    )

    default_timezone: str | None = None

    enable_task_assistance: bool | None = None
    enable_policy_assistance: bool | None = None
    enable_sentiment_analysis: bool | None = None

    @field_validator("default_timezone")
    @classmethod
    def validate_default_timezone(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        timezone = value.strip()

        try:
            ZoneInfo(timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError("Invalid IANA timezone") from error

        return timezone
