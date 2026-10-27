from app.ai.capabilities.text_generation import (
    TextGenerationRequest,
    TextGenerationResponse,
)


class MockAIProvider:
    def __init__(
        self,
        content: str,
        model: str = "mock-model",
    ) -> None:
        self.content = content
        self.model = model
        self.requests: list[TextGenerationRequest] = []

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        self.requests.append(request)

        return TextGenerationResponse(
            content=self.content,
            model=self.model,
        )