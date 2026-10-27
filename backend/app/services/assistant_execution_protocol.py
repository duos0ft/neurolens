from typing import Protocol

from app.ai.capabilities.text_generation import GenerationMessage
from app.services.assistant_execution_result import AssistantExecutionResult


class AssistantExecutionProtocol(Protocol):
    async def execute(
        self,
        message: str,
        history: list[GenerationMessage] | None = None,
    ) -> AssistantExecutionResult: ...