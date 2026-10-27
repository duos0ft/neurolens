from dataclasses import dataclass

from app.ai.capabilities.text_generation import TextGenerationResponse
from app.ai.capabilities.types import AICapability


@dataclass(frozen=True)
class AssistantExecutionResult:
    response: TextGenerationResponse
    capabilities: tuple[AICapability, ...]