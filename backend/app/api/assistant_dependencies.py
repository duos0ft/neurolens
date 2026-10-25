from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.registry import AIProviderRegistry
from app.ai.resolver import resolve_ai_provider_registry
from app.core.auth import get_current_employee
from app.core.database import get_db
from app.models.employee import Employee
from app.services.assistant_config_service import AssistantConfigService
from app.services.assistant_orchestrator import AssistantOrchestrator


def get_ai_provider_registry() -> AIProviderRegistry:
    return resolve_ai_provider_registry()


async def get_assistant_orchestrator(
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[AsyncSession, Depends(get_db)],
    registry: Annotated[
        AIProviderRegistry,
        Depends(get_ai_provider_registry),
    ],
) -> AssistantOrchestrator:
    config_service = AssistantConfigService(db)

    config = await config_service.get_config(
        employee_id=employee.user_id,
    )

    return AssistantOrchestrator(
        registry=registry,
        config=config,
    )