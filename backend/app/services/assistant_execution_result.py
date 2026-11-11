import uuid
from dataclasses import dataclass

from app.ai.capabilities.task_extraction import (
    TaskExtractionResult,
)
from app.ai.capabilities.text_generation import TextGenerationResponse
from app.ai.capabilities.types import AICapability
from app.services.conversation_context_snapshot import (
    ConversationContextSnapshot,
)
from app.services.policy_answer import PolicyAnswerStatus, PolicyCitation


@dataclass(frozen=True)
class AssistantTaskSuggestions:
    source_message_id: uuid.UUID | None
    extraction: TaskExtractionResult


@dataclass(frozen=True)
class AssistantExecutionResult:
    response: TextGenerationResponse
    capabilities: tuple[AICapability, ...]
    sources: tuple[ConversationContextSnapshot, ...] = ()
    task_suggestions: AssistantTaskSuggestions | None = None
    policy_status: PolicyAnswerStatus | None = None
    citations: tuple[PolicyCitation, ...] = ()
