from app.ai.capabilities.text_generation import (
    GenerationMessage,
    TextGenerationResponse,
)
from app.ai.capabilities.types import AICapability
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

    @property
    def title_provider(self):
        return self.orchestrator.registry.get_text_generation(
            AICapability.CONVERSATION_TITLE,
        )

    async def respond(
        self,
        message: str,
        history: list[GenerationMessage] | None = None,
    ) -> TextGenerationResponse:
        results = await self.orchestrator.respond(
            message=message,
            history=history,
        )

        return self.composer.compose(results)