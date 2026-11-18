import json

import pytest

from app.ai.capabilities.text_generation import (
    GenerationMessage,
    TextGenerationRequest,
    TextGenerationResponse,
)
from app.ai.capabilities.types import AICapability
from app.ai.registry import AIProviderRegistry
from app.services.assistant.assistant_config import AssistantConfig
from app.services.assistant.assistant_orchestrator import (
    AssistantOrchestrator,
    CapabilityClassificationError,
)


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


def classification_response(
    *intents: tuple[str, str],
) -> str:
    return json.dumps(
        {
            "intents": [
                {
                    "capability": capability,
                    "instruction": instruction,
                    "source_text": None,
                }
                for capability, instruction in intents
            ],
        }
    )


def explanation_response(
    explanation: str,
    ambiguities: list[str] | None = None,
    steps: list[str] | None = None,
    next_step: str | None = None,
) -> str:
    return json.dumps(
        {
            "explanation": explanation,
            "ambiguities": ambiguities if ambiguities is not None else [],
            "steps": steps if steps is not None else [],
            "next_step": next_step,
        }
    )


@pytest.mark.asyncio
async def test_orchestrator_executes_multiple_capabilities() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider(
        classification_response(
            (
                "message_explanation",
                "Explain the manager's message.",
            ),
            (
                "task_assistance",
                "Create a task list from the manager's message.",
            ),
        )
    )

    explanation = MockProvider(
        explanation_response(
            "The manager wants a progress update.",
        )
    )

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

    assert results[0].structured_explanation is not None

    assert results[0].structured_explanation.explanation == "The manager wants a progress update."

    assert results[0].structured_explanation.ambiguities == []
    assert results[0].structured_explanation.steps == []
    assert results[0].structured_explanation.next_step is None

    assert results[1].response.content == ("1. Check progress. 2. Report blockers.")

    assert results[1].structured_explanation is None

    assert len(classifier.requests) == 1
    assert len(explanation.requests) == 1
    assert len(tasks.requests) == 1

    assert "Explain the manager's message." in (explanation.requests[0].messages[0].content)

    assert "Create a task list" in (tasks.requests[0].messages[0].content)


@pytest.mark.asyncio
async def test_disabled_task_assistance_preserves_explanation() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider(
        classification_response(
            (
                "message_explanation",
                "Explain the meaning of the message.",
            ),
            (
                "task_assistance",
                "Create a task list.",
            ),
        )
    )

    explanation = MockProvider(
        explanation_response(
            "This message requests an update.",
        )
    )

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

    assert results[0].structured_explanation is not None
    assert results[0].structured_explanation.explanation == "This message requests an update."

    assert len(classifier.requests) == 1
    assert len(explanation.requests) == 1
    assert len(tasks.requests) == 0


@pytest.mark.asyncio
async def test_invalid_classification_does_not_execute_capabilities() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider("invalid JSON")

    explanation = MockProvider(
        explanation_response(
            "Should not execute.",
        )
    )

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

    with pytest.raises(
        CapabilityClassificationError,
        match="Unable to classify the employee's request",
    ):
        await orchestrator.respond("Explain this message and make a task list.")

    assert len(classifier.requests) == 2
    assert len(explanation.requests) == 0
    assert len(tasks.requests) == 0


@pytest.mark.asyncio
async def test_policy_question_does_not_call_generation_provider() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider(
        classification_response(
            (
                "policy_question",
                "Identify the company-specific annual leave question.",
            ),
        )
    )

    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION,
        classifier,
    )

    orchestrator = AssistantOrchestrator(registry)

    results = await orchestrator.respond("How many annual leave days does our company provide?")

    assert len(results) == 1
    assert results[0].capability == AICapability.POLICY_QUESTION
    assert "can't verify" in results[0].response.content
    assert results[0].response.model == "neurolens"
    assert results[0].structured_explanation is None
    assert len(classifier.requests) == 1


@pytest.mark.asyncio
async def test_mixed_policy_request_does_not_call_generation_provider() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider(
        classification_response(
            (
                "message_explanation",
                "Explain the HR message without answering policy questions.",
            ),
            (
                "policy_question",
                "Identify the request for leave entitlement.",
            ),
        )
    )

    explanation = MockProvider(
        explanation_response(
            "This should not be generated.",
        )
    )

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

    orchestrator = AssistantOrchestrator(registry)

    results = await orchestrator.respond(
        "Explain this HR message and tell me our leave entitlement."
    )

    assert len(results) == 1
    assert results[0].capability == AICapability.POLICY_QUESTION
    assert "can't safely separate" in results[0].response.content

    assert len(classifier.requests) == 1
    assert len(explanation.requests) == 0
    assert len(tasks.requests) == 0


@pytest.mark.asyncio
async def test_disabled_task_assistance_does_not_block_explanation() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider(
        classification_response(
            (
                "message_explanation",
                "Explain the manager's request.",
            ),
            (
                "task_assistance",
                "Break the request into tasks.",
            ),
        )
    )

    explanation = MockProvider(
        explanation_response(
            "Your manager wants a status update.",
        )
    )

    tasks = MockProvider("Should not be called")

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

    results = await orchestrator.respond("Explain this message and break it into tasks.")

    assert len(results) == 1
    assert results[0].capability == AICapability.MESSAGE_EXPLANATION

    assert results[0].structured_explanation is not None
    assert results[0].structured_explanation.explanation == "Your manager wants a status update."

    assert len(explanation.requests) == 1
    assert len(tasks.requests) == 0


@pytest.mark.asyncio
async def test_general_conversation_uses_general_provider() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider(
        classification_response(
            (
                "general_conversation",
                "Respond to the employee's greeting.",
            ),
        )
    )

    general = MockProvider("Hello! How can I help?")

    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION,
        classifier,
    )

    registry.register_text_generation(
        AICapability.GENERAL_CONVERSATION,
        general,
    )

    orchestrator = AssistantOrchestrator(registry)

    results = await orchestrator.respond("Hello!")

    assert len(results) == 1
    assert results[0].capability == AICapability.GENERAL_CONVERSATION
    assert results[0].response.content == "Hello! How can I help?"
    assert results[0].structured_explanation is None
    assert len(general.requests) == 1


@pytest.mark.asyncio
async def test_general_conversation_is_removed_from_mixed_requests() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider(
        classification_response(
            (
                "general_conversation",
                "Respond to the employee.",
            ),
            (
                "message_explanation",
                "Explain the meaning of EOD.",
            ),
        )
    )

    general = MockProvider("General response.")

    explanation = MockProvider(
        explanation_response(
            "EOD means end of day.",
        )
    )

    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION,
        classifier,
    )

    registry.register_text_generation(
        AICapability.GENERAL_CONVERSATION,
        general,
    )

    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        explanation,
    )

    orchestrator = AssistantOrchestrator(registry)

    results = await orchestrator.respond("Hello, what does EOD mean in this message?")

    assert len(results) == 1
    assert results[0].capability == AICapability.MESSAGE_EXPLANATION

    assert results[0].structured_explanation is not None
    assert results[0].structured_explanation.explanation == "EOD means end of day."

    assert len(general.requests) == 0
    assert len(explanation.requests) == 1


@pytest.mark.asyncio
async def test_empty_classification_does_not_execute_providers() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider(classification_response())

    explanation = MockProvider(
        explanation_response(
            "Should not execute.",
        )
    )

    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION,
        classifier,
    )

    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        explanation,
    )

    orchestrator = AssistantOrchestrator(registry)

    with pytest.raises(
        CapabilityClassificationError,
        match="Unable to classify the employee's request",
    ):
        await orchestrator.respond("Can you help me?")

    assert len(classifier.requests) == 2
    assert len(explanation.requests) == 0


@pytest.mark.asyncio
async def test_mixed_policy_request_uses_isolated_source() -> None:
    registry = AIProviderRegistry()

    source = "Please send me your availability."

    classifier = MockProvider(
        json.dumps(
            {
                "intents": [
                    {
                        "capability": "message_explanation",
                        "instruction": "Explain the manager's message.",
                        "source_text": source,
                    },
                    {
                        "capability": "policy_question",
                        "instruction": "Identify the annual leave question.",
                        "source_text": None,
                    },
                ],
            }
        )
    )

    explanation = MockProvider(
        explanation_response(
            "Your manager is asking when you are available.",
        )
    )

    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION,
        classifier,
    )

    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        explanation,
    )

    orchestrator = AssistantOrchestrator(registry)

    results = await orchestrator.respond(
        f'My manager wrote: "{source}" Explain it and tell me our annual leave entitlement.'
    )

    assert [result.capability for result in results] == [
        AICapability.MESSAGE_EXPLANATION,
        AICapability.POLICY_QUESTION,
    ]

    assert results[0].structured_explanation is not None

    assert (
        results[0].structured_explanation.explanation
        == "Your manager is asking when you are available."
    )

    assert len(explanation.requests) == 1

    sent_content = explanation.requests[0].messages[0].content

    assert source in sent_content
    assert "annual leave entitlement" not in sent_content

    assert "can't verify" in results[1].response.content


@pytest.mark.asyncio
async def test_mixed_policy_request_without_source_does_not_generate() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider(
        classification_response(
            (
                "message_explanation",
                "Explain the HR message.",
            ),
            (
                "policy_question",
                "Identify the leave entitlement question.",
            ),
        )
    )

    explanation = MockProvider(
        explanation_response(
            "Should not be generated.",
        )
    )

    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION,
        classifier,
    )

    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        explanation,
    )

    orchestrator = AssistantOrchestrator(registry)

    results = await orchestrator.respond(
        "Explain this HR message and tell me our leave entitlement."
    )

    assert len(results) == 1
    assert results[0].capability == AICapability.POLICY_QUESTION
    assert len(explanation.requests) == 0


@pytest.mark.asyncio
async def test_orchestrator_applies_employee_preferences() -> None:
    registry = AIProviderRegistry()

    explanation = MockProvider(
        explanation_response(
            "Your manager wants a progress update.",
        )
    )

    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        explanation,
    )

    orchestrator = AssistantOrchestrator(
        registry=registry,
        config=AssistantConfig(
            directness="high",
            response_length="short",
            highlight_ambiguity=False,
            step_by_step_guidance=False,
            always_show_next_step=False,
        ),
    )

    results = await orchestrator.execute(
        message="What does my manager mean by EOD?",
        capabilities=[
            AICapability.MESSAGE_EXPLANATION,
        ],
    )

    assert len(results) == 1
    assert len(explanation.requests) == 1

    assert results[0].structured_explanation is not None

    instructions = explanation.requests[0].system_instructions

    assert instructions is not None
    assert "Be direct, explicit, and concise" in instructions
    assert "1 to 2 sentences" in instructions
    assert "Prefer concise natural-language explanations" in instructions
    assert "Do not proactively add ambiguity analysis" in instructions
    assert "Do not automatically append a next-step recommendation" in instructions

    assert '"explanation"' in instructions
    assert '"ambiguities"' in instructions
    assert '"steps"' in instructions
    assert '"next_step"' in instructions


@pytest.mark.asyncio
async def test_explanation_follow_up_receives_recent_history() -> None:
    registry = AIProviderRegistry()

    classifier = MockProvider(
        classification_response(
            (
                "message_explanation",
                "Simplify the previous explanation.",
            ),
        )
    )

    explanation = MockProvider(
        explanation_response(
            "Your manager wants you to help, but not spend all day on it.",
        )
    )

    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION,
        classifier,
    )

    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        explanation,
    )

    orchestrator = AssistantOrchestrator(
        registry=registry,
    )

    history = [
        GenerationMessage(
            role="user",
            content='Explain "Help the new hire, but not all day."',
        ),
        GenerationMessage(
            role="assistant",
            content="Your manager is asking you to help the new hire.",
        ),
    ]

    results = await orchestrator.respond(
        message="Can you make that simpler?",
        history=history,
    )

    assert len(results) == 1
    assert results[0].capability == AICapability.MESSAGE_EXPLANATION

    assert results[0].structured_explanation is not None

    assert (
        results[0].structured_explanation.explanation
        == "Your manager wants you to help, but not spend all day on it."
    )

    request = explanation.requests[0]

    assert len(request.messages) == 3
    assert request.messages[0].content == history[0].content
    assert request.messages[1].content == history[1].content
    assert "Can you make that simpler?" in request.messages[2].content
