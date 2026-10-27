from app.ai.capabilities.text_generation import (
    GenerationMessage,
    TextGenerationResponse,
)
from app.services.assistant_execution_result import AssistantExecutionResult
from app.services.assistant_orchestrator import AssistantOrchestrator
from app.services.assistant_response_composer import AssistantResponseComposer


class OrchestratedAssistantService:
    def __init__(
        self,
        orchestrator: AssistantOrchestrator,
        composer: AssistantResponseComposer,
    ) -> None:
        self.orchestrator = orchestrator
        self.composer = composer

    async def execute(
        self,
        message: str,
        history: list[GenerationMessage] | None = None,
    ) -> AssistantExecutionResult:
        results = await self.orchestrator.respond(
            message=message,
            history=history,
        )

        response = self.composer.compose(results)

        return AssistantExecutionResult(
            response=response,
            capabilities=tuple(result.capability for result in results),
        )

    async def respond(
        self,
        message: str,
        history: list[GenerationMessage] | None = None,
    ) -> TextGenerationResponse:
        result = await self.execute(
            message=message,
            history=history,
        )

        return result.response
