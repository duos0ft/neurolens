from dataclasses import dataclass
from typing import Literal, Protocol

EmbeddingPurpose = Literal["document", "query"]


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: list[list[float]]
    model: str


class EmbeddingError(Exception):
    """Raised when an embedding provider cannot complete a request."""


class EmbeddingProvider(Protocol):
    """Turns text into vectors.

    ``model_id`` must uniquely identify the vector space. Stored embeddings
    are only compared with query embeddings that share the same identifier,
    so switching provider or model never mixes incompatible vectors.
    """

    @property
    def model_id(self) -> str: ...

    async def embed(
        self,
        texts: list[str],
        purpose: EmbeddingPurpose,
    ) -> EmbeddingResult: ...
