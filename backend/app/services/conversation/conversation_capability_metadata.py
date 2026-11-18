from dataclasses import dataclass

from app.ai.capabilities.types import AICapability
from app.services.conversation.conversation_context_snapshot import (
    ConversationContextSnapshot,
)

METADATA_VERSION = 2

SUPPORTED_CAPABILITIES = {
    AICapability.GENERAL_CONVERSATION,
    AICapability.MESSAGE_EXPLANATION,
    AICapability.TASK_ASSISTANCE,
    AICapability.TASK_EXTRACTION,
    AICapability.CALENDAR_EXTRACTION,
    AICapability.POLICY_QUESTION,
}


@dataclass(frozen=True)
class ConversationCapabilityMetadata:
    capabilities: tuple[AICapability, ...]
    sources: tuple[ConversationContextSnapshot, ...] = ()

    def __post_init__(self) -> None:
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError("Duplicate capabilities are not allowed")

        if any(capability not in SUPPORTED_CAPABILITIES for capability in self.capabilities):
            raise ValueError("Unsupported execution capability")

        source_capabilities = [source.capability for source in self.sources]

        if len(set(source_capabilities)) != len(source_capabilities):
            raise ValueError("Duplicate source capabilities")

        if any(capability not in self.capabilities for capability in source_capabilities):
            raise ValueError("Source capability must belong to the execution result")

        # Policy referrals must never carry reusable source data.
        if AICapability.POLICY_QUESTION in self.capabilities and self.sources:
            raise ValueError("Policy-related responses cannot contain source snapshots")

    def to_dict(self) -> dict:
        return {
            "version": METADATA_VERSION,
            "capabilities": [capability.value for capability in self.capabilities],
            "sources": [source.to_dict() for source in self.sources],
        }

    @classmethod
    def from_dict(
        cls,
        value: dict,
    ) -> "ConversationCapabilityMetadata":
        if not isinstance(value, dict):
            raise ValueError("Invalid capability metadata")

        version = value.get("version")

        if type(version) is not int or version not in (1, 2):
            raise ValueError("Unsupported capability metadata version")

        raw_capabilities = value.get("capabilities")

        if not isinstance(raw_capabilities, list):
            raise ValueError("Invalid capability metadata")

        try:
            capabilities = tuple(AICapability(capability) for capability in raw_capabilities)

        except (ValueError, TypeError) as error:
            raise ValueError("Invalid execution capability") from error

        if version == 1:
            return cls(
                capabilities=capabilities,
            )

        raw_sources = value.get("sources")

        if not isinstance(raw_sources, list):
            raise ValueError("Invalid source metadata")

        try:
            sources = tuple(ConversationContextSnapshot.from_dict(source) for source in raw_sources)

        except (ValueError, TypeError, KeyError) as error:
            raise ValueError("Invalid source metadata") from error

        return cls(
            capabilities=capabilities,
            sources=sources,
        )
