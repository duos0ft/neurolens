import pytest

from app.ai.capabilities.types import AICapability
from app.services.capability_intent import CapabilityIntent
from app.services.conversation_context_snapshot import (
    ConversationContextSnapshot,
)
from app.services.conversation_snapshot_builder import (
    ConversationSnapshotBuilder,
)
from app.services.conversation_source import ConversationSourceResolver


def test_resolves_exact_quoted_source() -> None:
    message = 'My manager wrote "Please send the report by EOD." Can you explain it?'

    resolver = ConversationSourceResolver()

    source = resolver.resolve(
        message=message,
        source_text="Please send the report by EOD.",
    )

    assert source is not None
    assert source.text == "Please send the report by EOD."
    assert source.matches(message)


def test_unquoted_source_is_not_accepted() -> None:
    resolver = ConversationSourceResolver()

    source = resolver.resolve(
        message="Please send the report by EOD.",
        source_text="Please send the report by EOD.",
    )

    assert source is None


def test_invented_source_is_rejected() -> None:
    resolver = ConversationSourceResolver()

    source = resolver.resolve(
        message='My manager wrote "Send the report."',
        source_text="The report is due tomorrow.",
    )

    assert source is None


def test_curly_quotes_are_supported() -> None:
    resolver = ConversationSourceResolver()

    message = "My manager wrote “Please review the draft.”"

    source = resolver.resolve(
        message=message,
        source_text="Please review the draft.",
    )

    assert source is not None
    assert source.matches(message)


def test_builds_explanation_snapshot() -> None:
    message = 'Explain "Please submit the report by EOD."'

    intent = CapabilityIntent(
        capability=AICapability.MESSAGE_EXPLANATION,
        instruction="Explain the workplace message.",
        source_text="Please submit the report by EOD.",
    )

    builder = ConversationSnapshotBuilder()

    snapshot = builder.build(
        message=message,
        intent=intent,
    )

    assert snapshot is not None
    assert snapshot.capability == AICapability.MESSAGE_EXPLANATION
    assert snapshot.source.matches(message)

    restored = ConversationContextSnapshot.from_dict(snapshot.to_dict())

    assert restored == snapshot


def test_policy_intent_cannot_create_snapshot() -> None:
    builder = ConversationSnapshotBuilder()

    snapshot = builder.build(
        message='Explain "What is our annual leave policy?"',
        intent=CapabilityIntent(
            capability=AICapability.POLICY_QUESTION,
            instruction="Identify the policy question.",
            source_text="What is our annual leave policy?",
        ),
    )

    assert snapshot is None


def test_invalid_snapshot_offsets_are_rejected() -> None:
    with pytest.raises(ValueError):
        ConversationContextSnapshot.from_dict(
            {
                "version": 1,
                "capability": "message_explanation",
                "source": {
                    "text": "Hello",
                    "start": 10,
                    "end": 12,
                },
            }
        )


def test_boolean_offsets_are_rejected() -> None:
    with pytest.raises(ValueError):
        ConversationContextSnapshot.from_dict(
            {
                "version": 1,
                "capability": "message_explanation",
                "source": {
                    "text": "Hello",
                    "start": True,
                    "end": 5,
                },
            }
        )
