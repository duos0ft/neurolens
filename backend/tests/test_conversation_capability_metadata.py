import pytest

from app.ai.capabilities.types import AICapability
from app.services.conversation_capability_metadata import (
    ConversationCapabilityMetadata,
)


def test_capability_metadata_round_trip() -> None:
    metadata = ConversationCapabilityMetadata(
        capabilities=(
            AICapability.MESSAGE_EXPLANATION,
            AICapability.TASK_ASSISTANCE,
        ),
    )

    restored = ConversationCapabilityMetadata.from_dict(metadata.to_dict())

    assert restored == metadata


def test_unsupported_metadata_version() -> None:
    with pytest.raises(ValueError):
        ConversationCapabilityMetadata.from_dict(
            {
                "version": 99,
                "capabilities": ["message_explanation"],
            }
        )


def test_unknown_capability_is_rejected() -> None:
    with pytest.raises(ValueError):
        ConversationCapabilityMetadata.from_dict(
            {
                "version": 1,
                "capabilities": ["unknown_capability"],
            }
        )