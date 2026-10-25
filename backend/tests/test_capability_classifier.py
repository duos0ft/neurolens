import json

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
        self.requests: list[TextGenerationRequest] = []

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        self.requests.append(request)

        return TextGenerationResponse(
            content=self.content,
            model="mock-classifier",
        )


def classification_response(
    *intents: tuple[str, str],
) -> str:
    return json.dumps(
        {
            "intents": [
                {
                    "capability": capability,
                    "instruction": instruction,
                }
                for capability, instruction in intents
            ],
        }
    )


@pytest.mark.asyncio
async def test_classifies_message_explanation() -> None:
    provider = MockClassifierProvider(
        classification_response(
            (
                "message_explanation",
                "Explain the meaning of EOD in the manager's message.",
            ),
        )
    )

    classifier = CapabilityClassifier(provider)

    result = await classifier.classify("What does my manager mean by EOD?")

    assert result.capabilities == [
        AICapability.MESSAGE_EXPLANATION,
    ]

    assert len(result.intents) == 1
    assert result.intents[0].instruction == ("Explain the meaning of EOD in the manager's message.")

    assert len(provider.requests) == 1
    assert provider.requests[0].messages[0].role == "user"


@pytest.mark.asyncio
async def test_classifies_multiple_capabilities() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider(
            classification_response(
                (
                    "message_explanation",
                    "Explain the workplace message.",
                ),
                (
                    "task_assistance",
                    "Create a task list from the message.",
                ),
            )
        )
    )

    result = await classifier.classify("Explain this message and create a task list.")

    assert result.capabilities == [
        AICapability.MESSAGE_EXPLANATION,
        AICapability.TASK_ASSISTANCE,
    ]

    assert result.intents[0].instruction == ("Explain the workplace message.")

    assert result.intents[1].instruction == ("Create a task list from the message.")


@pytest.mark.asyncio
async def test_removes_duplicate_capabilities() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider(
            classification_response(
                (
                    "task_assistance",
                    "Organize the employee's work.",
                ),
                (
                    "task_assistance",
                    "Create a checklist.",
                ),
            )
        )
    )

    result = await classifier.classify("Help me organize my work.")

    assert result.capabilities == [
        AICapability.TASK_ASSISTANCE,
    ]

    assert len(result.intents) == 1
    assert result.intents[0].instruction == ("Organize the employee's work.")


@pytest.mark.asyncio
async def test_classifies_general_conversation() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider(
            classification_response(
                (
                    "general_conversation",
                    "Respond to the employee's greeting.",
                ),
            )
        )
    )

    result = await classifier.classify("Hello!")

    assert result.capabilities == [
        AICapability.GENERAL_CONVERSATION,
    ]


@pytest.mark.asyncio
async def test_classifies_policy_question() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider(
            classification_response(
                (
                    "policy_question",
                    "Identify the company-specific annual leave question.",
                ),
            )
        )
    )

    result = await classifier.classify("How many annual leave days does our company provide?")

    assert result.capabilities == [
        AICapability.POLICY_QUESTION,
    ]


@pytest.mark.asyncio
async def test_rejects_invalid_classifier_output() -> None:
    classifier = CapabilityClassifier(MockClassifierProvider("not valid JSON"))

    with pytest.raises(
        ValueError,
        match="Unable to interpret capability classification",
    ):
        await classifier.classify("Explain this task.")


@pytest.mark.asyncio
async def test_rejects_old_array_format() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider('["message_explanation", "task_assistance"]')
    )

    with pytest.raises(
        ValueError,
        match="Unable to interpret capability classification",
    ):
        await classifier.classify("Explain this message and create a checklist.")


@pytest.mark.asyncio
async def test_rejects_missing_intents_array() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider('{"capability": "message_explanation"}')
    )

    with pytest.raises(
        ValueError,
        match="Unable to interpret capability classification",
    ):
        await classifier.classify("Explain this message.")


@pytest.mark.asyncio
async def test_rejects_unsupported_capability() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider(
            classification_response(
                (
                    "sentiment_analysis",
                    "Classify the employee's emotional state.",
                ),
            )
        )
    )

    with pytest.raises(
        ValueError,
        match="Unable to interpret capability classification",
    ):
        await classifier.classify("Analyze this employee's sentiment.")


@pytest.mark.asyncio
async def test_rejects_missing_instruction() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider(
            json.dumps(
                {
                    "intents": [
                        {
                            "capability": "message_explanation",
                        },
                    ],
                }
            )
        )
    )

    with pytest.raises(
        ValueError,
        match="Unable to interpret capability classification",
    ):
        await classifier.classify("Explain this message.")


@pytest.mark.asyncio
async def test_rejects_empty_instruction() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider(
            classification_response(
                (
                    "message_explanation",
                    "   ",
                ),
            )
        )
    )

    with pytest.raises(
        ValueError,
        match="Unable to interpret capability classification",
    ):
        await classifier.classify("Explain this message.")


@pytest.mark.asyncio
async def test_rejects_instruction_over_maximum_length() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider(
            classification_response(
                (
                    "message_explanation",
                    "A" * 501,
                ),
            )
        )
    )

    with pytest.raises(
        ValueError,
        match="Unable to interpret capability classification",
    ):
        await classifier.classify("Explain this message.")


@pytest.mark.asyncio
async def test_normalizes_instruction_whitespace() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider(
            classification_response(
                (
                    "message_explanation",
                    "  Explain   the message\n clearly.  ",
                ),
            )
        )
    )

    result = await classifier.classify("Explain this workplace message.")

    assert result.intents[0].instruction == ("Explain the message clearly.")


@pytest.mark.asyncio
async def test_rejects_empty_employee_message() -> None:
    provider = MockClassifierProvider(
        classification_response(
            (
                "general_conversation",
                "Respond to the employee.",
            ),
        )
    )

    classifier = CapabilityClassifier(provider)

    with pytest.raises(
        ValueError,
        match="Message cannot be empty",
    ):
        await classifier.classify("   ")

    assert provider.requests == []


@pytest.mark.asyncio
async def test_extracts_exact_source_text() -> None:
    source = "Please circle back before EOD."

    classifier = CapabilityClassifier(
        MockClassifierProvider(
            json.dumps(
                {
                    "intents": [
                        {
                            "capability": "message_explanation",
                            "instruction": "Explain the message.",
                            "source_text": source,
                        },
                    ],
                }
            )
        )
    )

    result = await classifier.classify(f'My manager wrote: "{source}" Can you explain it?')

    assert result.intents[0].source_text == source


@pytest.mark.asyncio
async def test_rejects_invented_source_text() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider(
            json.dumps(
                {
                    "intents": [
                        {
                            "capability": "message_explanation",
                            "instruction": "Explain the message.",
                            "source_text": "Finish everything by 3 PM.",
                        },
                    ],
                }
            )
        )
    )

    with pytest.raises(
        ValueError,
        match="Unable to interpret capability classification",
    ):
        await classifier.classify("My manager asked for a progress update.")


@pytest.mark.asyncio
async def test_accepts_null_source_text() -> None:
    classifier = CapabilityClassifier(
        MockClassifierProvider(
            json.dumps(
                {
                    "intents": [
                        {
                            "capability": "general_conversation",
                            "instruction": "Respond to the greeting.",
                            "source_text": None,
                        },
                    ],
                }
            )
        )
    )

    result = await classifier.classify("Hello!")

    assert result.intents[0].source_text is None