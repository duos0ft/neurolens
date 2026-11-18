import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.application_settings import ApplicationSettings
from app.models.employee_profile import EmployeeProfile
from app.services.assistant.assistant_config_service import AssistantConfigService


@pytest.mark.asyncio
async def test_assistant_configuration_uses_saved_preferences(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    async with test_session_factory() as db:
        profile = await db.get(EmployeeProfile, employee_id)

        if profile is None:
            profile = EmployeeProfile(
                user_id=employee_id,
            )
            db.add(profile)

        profile.directness = "high"
        profile.response_length = "short"
        profile.highlight_ambiguity = False
        profile.step_by_step_guidance = False
        profile.always_show_next_step = False

        await db.commit()

        service = AssistantConfigService(db)
        config = await service.get_config(employee_id)

        assert config.directness == "high"
        assert config.response_length == "short"
        assert config.highlight_ambiguity is False
        assert config.step_by_step_guidance is False
        assert config.always_show_next_step is False

        application_settings = await db.get(ApplicationSettings, 1)

        assert application_settings is not None
        assert config.enable_task_assistance == application_settings.enable_task_assistance
