from dataclasses import dataclass, field

from app.ai.capabilities.text_generation import GenerationMessage
from app.ai.capabilities.types import AICapability


@dataclass(frozen=True)
class TrustedConversationContext:
    by_capability: dict[
        AICapability,
        tuple[GenerationMessage, ...],
    ] = field(default_factory=dict)

    def for_capability(
        self,
        capability: AICapability,
    ) -> list[GenerationMessage]:
        return list(self.by_capability.get(capability, ()))