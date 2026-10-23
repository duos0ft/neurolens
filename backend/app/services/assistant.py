from app.ai.capabilities.text_generation import (
    GenerationMessage,
    TextGenerationProvider,
    TextGenerationRequest,
    TextGenerationResponse,
)


class AssistantService:
    def __init__(
        self,
        provider: TextGenerationProvider,
    ) -> None:
        self.provider = provider

    async def respond(
        self,
        message: str,
    ) -> TextGenerationResponse:
        if not message.strip():
            raise ValueError("Message cannot be empty")

        request = TextGenerationRequest(
            messages=[
                GenerationMessage(
                    role="user",
                    content=message.strip(),
                ),
            ],
            system_instructions=(
                "You are NeuroLens, an AI workplace assistant. "
                "Help employees understand workplace communication "
                "using clear, respectful, and actionable language. "
                "Do not invent company policies, deadlines, or facts. "
                "When information is unclear, explain what is missing."
            ),
        )

        return await self.provider.generate(request)
