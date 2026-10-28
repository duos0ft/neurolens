from types import SimpleNamespace

from app.ai.capabilities.types import AICapability
from app.services.verified_conversation_context import (
    VerifiedConversationContextResolver,
)


def make_message(
    role: str,
    content: str,
    metadata: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        role=role,
        content=content,
        capability_metadata=metadata,
    )


def make_metadata(
    message: str,
    source: str,
    capability: str = "message_explanation",
) -> dict:
    start = message.index(source)

    return {
        "version": 2,
        "capabilities": [capability],
        "sources": [
            {
                "version": 1,
                "capability": capability,
                "source": {
                    "text": source,
                    "start": start,
                    "end": start + len(source),
                },
            },
        ],
    }


def test_retrieves_verified_quoted_source() -> None:
    resolver = VerifiedConversationContextResolver()

    message = 'Explain "Please submit the report by EOD."'

    history = [
        make_message("user", message),
        make_message(
            "assistant",
            "EOD means end of day.",
            make_metadata(
                message,
                "Please submit the report by EOD.",
            ),
        ),
    ]

    result = resolver.resolve(
        AICapability.MESSAGE_EXPLANATION,
        history,
    )

    assert result.sources == ("Please submit the report by EOD.",)


def test_rejects_invalid_source_offsets() -> None:
    resolver = VerifiedConversationContextResolver()

    message = 'Explain "Please review the report."'

    metadata = make_metadata(
        message,
        "Please review the report.",
    )

    metadata["sources"][0]["source"]["start"] = 0

    history = [
        make_message("user", message),
        make_message(
            "assistant",
            "Please review the report.",
            metadata,
        ),
    ]

    result = resolver.resolve(
        AICapability.MESSAGE_EXPLANATION,
        history,
    )

    assert result.sources == ()


def test_rejects_legacy_metadata() -> None:
    resolver = VerifiedConversationContextResolver()

    history = [
        make_message(
            "user",
            "Explain this message.",
        ),
        make_message(
            "assistant",
            "Here is an explanation.",
            {
                "version": 1,
                "capabilities": ["message_explanation"],
            },
        ),
    ]

    result = resolver.resolve(
        AICapability.MESSAGE_EXPLANATION,
        history,
    )

    assert result.sources == ()


def test_rejects_mixed_capability_metadata() -> None:
    resolver = VerifiedConversationContextResolver()

    message = 'Explain "Finish the report."'

    metadata = make_metadata(
        message,
        "Finish the report.",
    )

    metadata["capabilities"].append("task_assistance")

    history = [
        make_message("user", message),
        make_message(
            "assistant",
            "Explanation and task plan.",
            metadata,
        ),
    ]

    result = resolver.resolve(
        AICapability.MESSAGE_EXPLANATION,
        history,
    )

    assert result.sources == ()


def test_policy_questions_have_no_reusable_context() -> None:
    resolver = VerifiedConversationContextResolver()

    result = resolver.resolve(
        AICapability.POLICY_QUESTION,
        [],
    )

    assert result.sources == ()


def test_different_capability_cannot_reuse_source() -> None:
    resolver = VerifiedConversationContextResolver()

    message = 'Explain "Please review this draft."'

    history = [
        make_message("user", message),
        make_message(
            "assistant",
            "Your manager wants you to review the draft.",
            make_metadata(
                message,
                "Please review this draft.",
            ),
        ),
    ]

    result = resolver.resolve(
        AICapability.TASK_ASSISTANCE,
        history,
    )

    assert result.sources == ()
