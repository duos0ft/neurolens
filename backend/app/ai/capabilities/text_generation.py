from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GenerationMessage:
    role: str
    content: str


@dataclass(frozen=True)
class TextGenerationRequest:
    messages: list[GenerationMessage]
    system_instructions: str | None = None


@dataclass(frozen=True)
class TextGenerationResponse:
    content: str
    model: str


class TextGenerationProvider(Protocol):
    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        ...
