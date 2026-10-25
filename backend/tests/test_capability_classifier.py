import pytest

from app.ai.capabilities.text_generation import (
    TextGenerationRequest,
    TextGenerationResponse,
)
from app.ai.capabilities.types import AICapability
from app.services.capability_classifier import CapabilityClassifier


class MockClassifierProvider:
    def __init__(self, content: str) -> None:
        self.content = content

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        return TextGenerationResponse(
            content=self.content,
            model="mock-classifier",
        )


@pytest.mark.asyncio
async def test_classifies_message_explanation() -> None:
    classifier = CapabilityClassifier(MockClassifierProvider('["message_explanation"]'))

    result = await classifier.classify("What does my manager mean by EOD?")

    assert result.capabilities == [
        AICapability.MESSAGE_EXPLANATION,
    ]


@pytest.mark.asyncio
async def test_classifies_multiple_capabilities() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider('["message_explanation", "task_assistance"]')
    )

    result = await classifier.classify("Explain this message and create a task list.")

    assert result.capabilities == [
        AICapability.MESSAGE_EXPLANATION,
        AICapability.TASK_ASSISTANCE,
    ]


@pytest.mark.asyncio
async def test_removes_duplicate_capabilities() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider('["task_assistance", "task_assistance"]')
    )

    result = await classifier.classify("Help me organize my work.")

    assert result.capabilities == [
        AICapability.TASK_ASSISTANCE,
    ]


@pytest.mark.asyncio
async def test_rejects_invalid_classifier_output() -> None:
    classifier = CapabilityClassifier(MockClassifierProvider("not valid JSON"))

    with pytest.raises(
        ValueError,
        match="Unable to interpret capability classification",
    ):
        await classifier.classify("Explain this task.")