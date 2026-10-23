import pytest

from app.ai.capabilities.text_generation import (
    TextGenerationRequest,
    TextGenerationResponse,
)
from app.services.assistant import AssistantService


class MockTextGenerationProvider:
    def __init__(self) -> None:
        self.last_request: TextGenerationRequest | None = None

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        self.last_request = request

        return TextGenerationResponse(
            content="Please prepare the report and send it by Friday.",
            model="mock-model",
        )


@pytest.mark.asyncio
async def test_assistant_uses_configured_provider() -> None:
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider=provider)

    response = await assistant.respond("Explain my manager's instructions.")

    assert response.content == "Please prepare the report and send it by Friday."
    assert response.model == "mock-model"

    assert provider.last_request is not None
    assert provider.last_request.messages[0].role == "user"
    assert provider.last_request.messages[0].content == "Explain my manager's instructions."
    assert provider.last_request.system_instructions is not None


@pytest.mark.asyncio
async def test_assistant_rejects_empty_messages() -> None:
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider=provider)

    with pytest.raises(ValueError, match="Message cannot be empty"):
        await assistant.respond("   ")

    assert provider.last_request is None
