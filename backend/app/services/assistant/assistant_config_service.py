import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_settings import ApplicationSettings
from app.models.employee_profile import EmployeeProfile
from app.services.assistant.assistant_config import AssistantConfig


class AssistantConfigService:
    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def get_config(
        self,
        employee_id: uuid.UUID,
    ) -> AssistantConfig:
        settings = await self.db.get(ApplicationSettings, 1)

        if settings is None:
            raise RuntimeError("Application settings are not configured")

        profile = await self.db.scalar(
            select(EmployeeProfile).where(
                EmployeeProfile.user_id == employee_id,
            )
        )

        return AssistantConfig(
            enable_task_assistance=settings.enable_task_assistance,
            enable_policy_assistance=settings.enable_policy_assistance,
            enable_sentiment_analysis=settings.enable_sentiment_analysis,
            directness=profile.directness if profile else "balanced",
            response_length=profile.response_length if profile else "medium",
            highlight_ambiguity=(profile.highlight_ambiguity if profile else True),
            step_by_step_guidance=(profile.step_by_step_guidance if profile else True),
            always_show_next_step=(profile.always_show_next_step if profile else True),
        )
