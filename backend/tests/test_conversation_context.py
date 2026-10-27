from app.ai.capabilities.text_generation import GenerationMessage
from app.ai.capabilities.types import AICapability
from app.services.conversation_context import (
    MAX_CONTEXT_MESSAGES,
    ConversationContextResolver,
)


def test_general_conversation_requires_trusted_context() -> None:
    resolver = ConversationContextResolver()

    history = [
        GenerationMessage(
            role="user",
            content="Hello.",
        ),
        GenerationMessage(
            role="assistant",
            content="Hi! How can I help?",
        ),
    ]

    result = resolver.resolve(
        capability=AICapability.GENERAL_CONVERSATION,
        history=history,
    )

    assert result.messages == []

    trusted_result = resolver.resolve(
        capability=AICapability.GENERAL_CONVERSATION,
        history=history,
        trusted_context=True,
    )

    assert trusted_result.messages == history


def test_policy_question_prevents_context_sharing() -> None:
    resolver = ConversationContextResolver()

    history = [
        GenerationMessage(
            role="user",
            content="What is our annual leave policy?",
        ),
    ]

    result = resolver.resolve(
        capability=AICapability.GENERAL_CONVERSATION,
        history=history,
        has_policy_question=True,
        trusted_context=True,
    )

    assert result.messages == []


def test_isolated_source_takes_priority_over_history() -> None:
    resolver = ConversationContextResolver()

    history = [
        GenerationMessage(
            role="user",
            content="Previous unrelated conversation.",
        ),
    ]

    result = resolver.resolve(
        capability=AICapability.MESSAGE_EXPLANATION,
        history=history,
        has_isolated_source=True,
        trusted_context=True,
    )

    assert result.messages == []


def test_specialized_capabilities_do_not_receive_unverified_history() -> None:
    resolver = ConversationContextResolver()

    history = [
        GenerationMessage(
            role="user",
            content="Previous workplace message.",
        ),
    ]

    for capability in [
        AICapability.MESSAGE_EXPLANATION,
        AICapability.TASK_ASSISTANCE,
    ]:
        result = resolver.resolve(
            capability=capability,
            history=history,
            trusted_context=True,
        )

        assert result.messages == []


def test_context_is_limited_to_recent_messages() -> None:
    resolver = ConversationContextResolver()

    history = [
        GenerationMessage(
            role="user",
            content=f"Message {index}",
        )
        for index in range(30)
    ]

    result = resolver.resolve(
        capability=AICapability.GENERAL_CONVERSATION,
        history=history,
        trusted_context=True,
    )

    assert len(result.messages) == MAX_CONTEXT_MESSAGES
    assert result.messages[0].content == "Message 20"
    assert result.messages[-1].content == "Message 29"
