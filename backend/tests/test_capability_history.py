from types import SimpleNamespace

from app.ai.capabilities.types import AICapability
from app.services.capability_history import CapabilityHistoryResolver


def make_message(
    role: str,
    content: str,
    capabilities: list[str] | None = None,
):
    metadata = None

    if capabilities is not None:
        metadata = {
            "version": 1,
            "capabilities": capabilities,
        }

    return SimpleNamespace(
        role=role,
        content=content,
        capability_metadata=metadata,
    )


def test_matching_explanation_history() -> None:
    resolver = CapabilityHistoryResolver()

    history = [
        make_message("user", "What does EOD mean?"),
        make_message(
            "assistant",
            "EOD means end of day.",
            ["message_explanation"],
        ),
    ]

    result = resolver.resolve(
        capability=AICapability.MESSAGE_EXPLANATION,
        history=history,
    )

    assert len(result.messages) == 2
    assert result.messages[0].content == "What does EOD mean?"
    assert result.messages[1].content == "EOD means end of day."


def test_different_capability_is_excluded() -> None:
    resolver = CapabilityHistoryResolver()

    history = [
        make_message("user", "Break this work into steps."),
        make_message(
            "assistant",
            "1. Review requirements.",
            ["task_assistance"],
        ),
    ]

    result = resolver.resolve(
        capability=AICapability.MESSAGE_EXPLANATION,
        history=history,
    )

    assert result.messages == []


def test_mixed_capability_history_is_excluded() -> None:
    resolver = CapabilityHistoryResolver()

    history = [
        make_message("user", "Explain and plan this work."),
        make_message(
            "assistant",
            "Explanation and suggested steps.",
            ["message_explanation", "task_assistance"],
        ),
    ]

    result = resolver.resolve(
        capability=AICapability.MESSAGE_EXPLANATION,
        history=history,
    )

    assert result.messages == []


def test_legacy_history_is_excluded() -> None:
    resolver = CapabilityHistoryResolver()

    history = [
        make_message("user", "Explain this message."),
        make_message("assistant", "Here is the explanation."),
    ]

    result = resolver.resolve(
        capability=AICapability.MESSAGE_EXPLANATION,
        history=history,
    )

    assert result.messages == []


def test_policy_context_is_never_forwarded() -> None:
    resolver = CapabilityHistoryResolver()

    history = [
        make_message("user", "What is our leave policy?"),
        make_message(
            "assistant",
            "Please contact HR.",
            ["policy_question"],
        ),
    ]

    result = resolver.resolve(
        capability=AICapability.POLICY_QUESTION,
        history=history,
    )

    assert result.messages == []


def test_context_stops_at_different_capability() -> None:
    resolver = CapabilityHistoryResolver()

    history = [
        make_message("user", "Explain the deadline."),
        make_message(
            "assistant",
            "The deadline is Friday.",
            ["message_explanation"],
        ),
        make_message("user", "Make a task plan."),
        make_message(
            "assistant",
            "1. Review the requirements.",
            ["task_assistance"],
        ),
        make_message("user", "Explain the latest message."),
        make_message(
            "assistant",
            "It describes the next action.",
            ["message_explanation"],
        ),
    ]

    result = resolver.resolve(
        capability=AICapability.MESSAGE_EXPLANATION,
        history=history,
    )

    assert len(result.messages) == 2
    assert result.messages[0].content == "Explain the latest message."