from dataclasses import dataclass

from app.ai.capabilities.types import AICapability


@dataclass(frozen=True)
class SourceOnlyContext:
    by_capability: dict[AICapability, tuple[str, ...]]

    def for_capability(
        self,
        capability: AICapability,
    ) -> tuple[str, ...]:
        return self.by_capability.get(capability, ())
