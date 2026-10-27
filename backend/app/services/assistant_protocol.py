from typing import Protocol

from app.ai.capabilities.text_generation import (
    GenerationMessage,
    TextGenerationResponse,
)


class AssistantProtocol(Protocol):
    async def respond(
        self,
        message: str,
        history: list[GenerationMessage] | None = None,
    ) -> TextGenerationResponse:
        ...