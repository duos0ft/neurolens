from dataclasses import dataclass
from typing import Literal

from app.ai.capabilities.types import AICapability


@dataclass(frozen=True)
class CapabilityIntent:
    capability: AICapability
    instruction: str
    source_text: str | None = None
    source_scope: Literal["current", "previous"] = "current"
