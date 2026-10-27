from dataclasses import dataclass

from app.ai.capabilities.types import AICapability


@dataclass(frozen=True)
class ConversationCapabilityMetadata:
    capabilities: tuple[AICapability, ...]

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "capabilities": [capability.value for capability in self.capabilities],
        }

    @classmethod
    def from_dict(
        cls,
        value: dict,
    ) -> "ConversationCapabilityMetadata":
        if value.get("version") != 1:
            raise ValueError("Unsupported capability metadata version")

        raw_capabilities = value.get("capabilities")

        if not isinstance(raw_capabilities, list):
            raise ValueError("Invalid capability metadata")

        capabilities = tuple(AICapability(capability) for capability in raw_capabilities)

        return cls(capabilities=capabilities)