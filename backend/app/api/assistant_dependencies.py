from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.embedding_factory import create_embedding_provider
from app.ai.registry import AIProviderRegistry, ProviderNotConfiguredError
from app.ai.resolver import resolve_ai_provider_registry
from app.core.auth import get_current_employee
from app.core.database import get_db
from app.models.employee import Employee
from app.services.assistant_config_service import AssistantConfigService
from app.services.assistant_orchestrator import AssistantOrchestrator
from app.services.assistant_response_composer import AssistantResponseComposer
from app.services.orchestrated_assistant import OrchestratedAssistantService
from app.services.policy_questions import PolicyQuestionService
from app.services.task_extraction import TaskExtractionService


def get_ai_provider_registry() -> AIProviderRegistry:
    try:
        return resolve_ai_provider_registry()

    except ProviderNotConfiguredError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI assistant is temporarily unavailable",
        ) from error


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

    policy_question_service = None

    if config.enable_policy_assistance:
        try:
            embedding_provider = create_embedding_provider()

            policy_question_service = PolicyQuestionService(
                db=db,
                embedding_provider=embedding_provider,
            )

        except ProviderNotConfiguredError:
            policy_question_service = None

    return AssistantOrchestrator(
        registry=registry,
        config=config,
        policy_question_service=policy_question_service,
    )


def get_orchestrated_assistant(
    orchestrator: Annotated[
        AssistantOrchestrator,
        Depends(get_assistant_orchestrator),
    ],
) -> OrchestratedAssistantService:
    return OrchestratedAssistantService(
        orchestrator=orchestrator,
        composer=AssistantResponseComposer(),
    )


def get_task_extraction_service(
    registry: Annotated[
        AIProviderRegistry,
        Depends(get_ai_provider_registry),
    ],
) -> TaskExtractionService:
    return TaskExtractionService(registry=registry)
