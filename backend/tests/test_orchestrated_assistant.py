import pytest

from app.ai.capabilities.text_generation import (
    TextGenerationRequest,
    TextGenerationResponse,
)
from app.ai.capabilities.types import AICapability
from app.ai.registry import AIProviderRegistry
from app.services.assistant_orchestrator import AssistantOrchestrator
from app.services.assistant_response_composer import AssistantResponseComposer
from app.services.orchestrated_assistant import OrchestratedAssistantService


class MockProvider:
    def __init__(self, content: str) -> None:
        self.content = content
        self.requests: list[TextGenerationRequest] = []

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        self.requests.append(request)

        return TextGenerationResponse(
            content=self.content,
            model="mock-model",
        )


@pytest.mark.asyncio
async def test_orchestrated_assistant_returns_composed_response() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider(
        '{"intents": ['
        '{"capability": "message_explanation", '
        '"instruction": "Explain the message.", '
        '"source_text": null}, '
        '{"capability": "task_assistance", '
        '"instruction": "Create a task list.", '
        '"source_text": null}'
        "]}"
    )

    explanation = MockProvider("Your manager wants an update.")
    tasks = MockProvider("1. Check progress.\n2. Report blockers.")
    title = MockProvider("Workplace communication")

    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION,
        classifier,
    )
    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        explanation,
    )
    registry.register_text_generation(
        AICapability.TASK_ASSISTANCE,
        tasks,
    )
    registry.register_text_generation(
        AICapability.CONVERSATION_TITLE,
        title,
    )

    orchestrator = AssistantOrchestrator(
        registry=registry,
        enable_task_assistance=True,
    )

    assistant = OrchestratedAssistantService(
        orchestrator=orchestrator,
        composer=AssistantResponseComposer(),
    )

    response = await assistant.respond("Explain this message and create a task list.")

    assert "**Message explanation**" in response.content
    assert "**Suggested steps**" in response.content
    assert "Your manager wants an update." in response.content
    assert "Check progress." in response.content

    assert assistant.title_provider is title

    assert len(classifier.requests) == 1
    assert len(explanation.requests) == 1
    assert len(tasks.requests) == 1
    assert len(title.requests) == 0