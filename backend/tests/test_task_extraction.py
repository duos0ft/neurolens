import pytest
from pydantic import ValidationError

from app.ai.capabilities.task_extraction import (
    TaskExtractionResult,
)


def test_valid_task_extraction() -> None:
    result = TaskExtractionResult.model_validate(
        {
            "tasks": [
                {
                    "title": "Review onboarding documentation",
                    "description": "Identify and correct outdated information.",
                    "priority": "low",
                    "due_date": None,
                    "source_text": "Review the onboarding documentation.",
                    "subtasks": [
                        {"title": "Identify outdated information"},
                        {"title": "Update incorrect sections"},
                    ],
                }
            ]
        }
    )

    assert len(result.tasks) == 1
    assert result.tasks[0].priority == "low"
    assert len(result.tasks[0].subtasks) == 2


def test_empty_extraction_is_valid() -> None:
    result = TaskExtractionResult.model_validate({"tasks": []})

    assert result.tasks == []


def test_invalid_priority_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TaskExtractionResult.model_validate(
            {
                "tasks": [
                    {
                        "title": "Review documentation",
                        "priority": "urgent-ish",
                    }
                ]
            }
        )


def test_missing_task_title_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TaskExtractionResult.model_validate(
            {
                "tasks": [
                    {
                        "description": "Review the documentation.",
                    }
                ]
            }
        )


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        TaskExtractionResult.model_validate(
            {
                "tasks": [
                    {
                        "title": "Review documentation",
                        "automatically_save": True,
                    }
                ]
            }
        )