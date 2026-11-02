import json

import pytest

from app.ai.capabilities.text_generation import (
    TextGenerationRequest,
    TextGenerationResponse,
)
from app.ai.capabilities.types import AICapability
from app.ai.registry import AIProviderRegistry
from app.services.task_extraction import (
    TaskExtractionError,
    TaskExtractionService,
)


class MockTaskExtractionProvider:
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


def create_service(
    content: str,
) -> tuple[TaskExtractionService, MockTaskExtractionProvider]:
    registry = AIProviderRegistry()
    provider = MockTaskExtractionProvider(content)

    registry.register_text_generation(
        AICapability.TASK_EXTRACTION,
        provider,
    )

    return TaskExtractionService(registry), provider


@pytest.mark.asyncio
async def test_extracts_individual_task_suggestions() -> None:
    source = "Review the feedback and send a summary by Friday."

    service, provider = create_service(
        json.dumps(
            {
                "tasks": [
                    {
                        "title": "Review client feedback",
                        "description": "Identify important issues.",
                        "priority": None,
                        "due_date": None,
                        "source_text": "Review the feedback",
                        "subtasks": [],
                    },
                    {
                        "title": "Send a summary",
                        "description": "Share the findings with the manager.",
                        "priority": None,
                        "due_date": None,
                        "source_text": "send a summary by Friday",
                        "subtasks": [],
                    },
                ]
            }
        )
    )

    result = await service.extract(source)

    assert len(result.tasks) == 2
    assert result.tasks[0].title == "Review client feedback"
    assert result.tasks[1].title == "Send a summary"

    assert result.tasks[0].priority is None
    assert result.tasks[1].due_date is None

    assert len(provider.requests) == 1
    assert provider.requests[0].messages[0].content == source


@pytest.mark.asyncio
async def test_extracts_parent_task_with_subtasks() -> None:
    service, _ = create_service(
        json.dumps(
            {
                "tasks": [
                    {
                        "title": "Update onboarding documentation",
                        "subtasks": [
                            {"title": "Review existing documentation"},
                            {"title": "Correct outdated information"},
                        ],
                    }
                ]
            }
        )
    )

    result = await service.extract("Review and update the onboarding documentation.")

    assert len(result.tasks) == 1
    assert len(result.tasks[0].subtasks) == 2


@pytest.mark.asyncio
async def test_accepts_empty_task_suggestions() -> None:
    service, _ = create_service(json.dumps({"tasks": []}))

    result = await service.extract("Thanks for your help today!")

    assert result.tasks == []


@pytest.mark.asyncio
async def test_discards_unverified_source_text() -> None:
    service, _ = create_service(
        json.dumps(
            {
                "tasks": [
                    {
                        "title": "Review documentation",
                        "source_text": "Complete the project by 3 PM.",
                    }
                ]
            }
        )
    )

    result = await service.extract("Please review the documentation.")

    assert result.tasks[0].source_text is None


@pytest.mark.asyncio
async def test_rejects_invalid_json() -> None:
    service, _ = create_service("invalid JSON")

    with pytest.raises(
        TaskExtractionError,
        match="Unable to validate task extraction response",
    ):
        await service.extract("Review the onboarding documentation.")


@pytest.mark.asyncio
async def test_rejects_invalid_task_data() -> None:
    service, _ = create_service(
        json.dumps(
            {
                "tasks": [
                    {
                        "title": "Review documentation",
                        "priority": "urgent-ish",
                    }
                ]
            }
        )
    )

    with pytest.raises(TaskExtractionError):
        await service.extract("Review the onboarding documentation.")


@pytest.mark.asyncio
async def test_rejects_empty_workplace_text() -> None:
    service, provider = create_service(json.dumps({"tasks": []}))

    with pytest.raises(
            ValueError,
            match="Workplace text cannot be empty",
    ):
        await service.extract("   ")

    assert provider.requests == []
