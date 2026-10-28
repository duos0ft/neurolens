import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.employee_profile import EmployeeProfile
from app.services.assistant_config_service import AssistantConfigService


@pytest.mark.asyncio
async def test_loads_default_employee_preferences(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    async with test_session_factory() as db:
        service = AssistantConfigService(db)

        config = await service.get_config(
            test_invitation.employee_id,
        )

        assert config.directness == "balanced"
        assert config.response_length == "medium"
        assert config.highlight_ambiguity is True
        assert config.step_by_step_guidance is True
        assert config.always_show_next_step is True
        assert config.enable_policy_assistance is False


@pytest.mark.asyncio
async def test_loads_saved_employee_preferences(
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
