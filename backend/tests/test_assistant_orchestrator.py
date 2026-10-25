import pytest

from app.ai.capabilities.text_generation import (
    TextGenerationRequest,
    TextGenerationResponse,
)
from app.ai.capabilities.types import AICapability
from app.ai.registry import AIProviderRegistry
from app.services.assistant_orchestrator import AssistantOrchestrator


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
async def test_orchestrator_executes_multiple_capabilities() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider('["message_explanation", "task_assistance"]')
    explanation = MockProvider("The manager wants a progress update.")
    tasks = MockProvider("1. Check progress. 2. Report blockers.")

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

    orchestrator = AssistantOrchestrator(
        registry=registry,
        enable_task_assistance=True,
    )

    results = await orchestrator.respond("Explain this message and make me a task list.")

    assert [result.capability for result in results] == [
        AICapability.MESSAGE_EXPLANATION,
        AICapability.TASK_ASSISTANCE,
    ]

    assert results[0].response.content == ("The manager wants a progress update.")
    assert results[1].response.content == ("1. Check progress. 2. Report blockers.")

    assert len(classifier.requests) == 1
    assert len(explanation.requests) == 1
    assert len(tasks.requests) == 1


@pytest.mark.asyncio
async def test_disabled_task_assistance_preserves_explanation() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider('["message_explanation", "task_assistance"]')
    explanation = MockProvider("This message requests an update.")
    tasks = MockProvider("This should not be generated.")

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

    orchestrator = AssistantOrchestrator(
        registry=registry,
        enable_task_assistance=False,
    )

    results = await orchestrator.respond("Explain this message and create a task list.")

    assert len(results) == 1
    assert results[0].capability == AICapability.MESSAGE_EXPLANATION
    assert len(explanation.requests) == 1
    assert len(tasks.requests) == 0


@pytest.mark.asyncio
async def test_invalid_classification_does_not_execute_capabilities() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider("invalid JSON")
    explanation = MockProvider("Should not execute")
    tasks = MockProvider("Should not execute")

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

    orchestrator = AssistantOrchestrator(
        registry=registry,
        enable_task_assistance=True,
    )

    results = await orchestrator.respond("Explain this message and make a task list.")

    assert results == []
    assert len(classifier.requests) == 1
    assert len(explanation.requests) == 0
    assert len(tasks.requests) == 0