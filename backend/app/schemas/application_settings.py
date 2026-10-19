from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApplicationSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_name: str
    enable_task_assistance: bool
    enable_policy_assistance: bool
    enable_sentiment_analysis: bool
    created_at: datetime
    updated_at: datetime


class UpdateApplicationSettingsRequest(BaseModel):
    organization_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    enable_task_assistance: bool | None = None
    enable_policy_assistance: bool | None = None
    enable_sentiment_analysis: bool | None = None
