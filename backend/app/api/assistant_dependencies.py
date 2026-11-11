import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.capabilities.types import AICapability
from app.ai.registry import AIProviderRegistry, ProviderNotConfiguredError
from app.ai.resolver import resolve_ai_provider_registry
from app.core.auth import get_current_employee
from app.core.database import get_db
from app.core.settings import settings
from app.models.employee import Employee
from app.services.assistant_config import AssistantConfig
from app.services.assistant_config_service import AssistantConfigService
from app.services.assistant_instructions import build_preference_instructions
from app.services.assistant_orchestrator import AssistantOrchestrator
from app.services.assistant_response_composer import AssistantResponseComposer
from app.services.knowledge_retrieval import DatabaseKnowledgeRetriever
from app.services.orchestrated_assistant import OrchestratedAssistantService
from app.services.policy_answer import PolicyAnswerService
from app.services.task_extraction import TaskExtractionService

logger = logging.getLogger(__name__)


def build_policy_answerer(
    db: AsyncSession,
    registry: AIProviderRegistry,
    config: AssistantConfig,
) -> PolicyAnswerService | None:
    """Create the grounded policy answerer, or None when it must stay off.

    Without an answerer the orchestrator refers policy questions to HR
    instead of answering them.
    """

    if not config.enable_policy_assistance:
        return None

    try:
        embedder = registry.get_embeddings()
        provider = registry.get_text_generation(AICapability.POLICY_GENERATION)

    except ProviderNotConfiguredError:
        logger.warning("Policy assistance is enabled but knowledge providers are not configured")
        return None

    return PolicyAnswerService(
        retriever=DatabaseKnowledgeRetriever(db, embedder),
        provider=provider,
        top_k=settings.knowledge_retrieval_top_k,
        min_score=settings.knowledge_min_relevance,
        preference_instructions=build_preference_instructions(config),
    )


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

    return AssistantOrchestrator(
        registry=registry,
        config=config,
        policy_answerer=build_policy_answerer(db, registry, config),
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
