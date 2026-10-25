from dataclasses import dataclass

from app.ai.capabilities.types import AICapability


@dataclass(frozen=True)
class CapabilityIntent:
    capability: AICapability
    instruction: str
    source_text: str | None = None