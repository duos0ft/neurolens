from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class GenerationMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True)
class TextGenerationRequest:
    messages: list[GenerationMessage]
    system_instructions: str | None = None


@dataclass(frozen=True)
class TextGenerationResponse:
    content: str
    model: str


class TextGenerationError(Exception):
    """Raised when a text generation provider cannot complete a request."""


class TextGenerationProvider(Protocol):
    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        ...
