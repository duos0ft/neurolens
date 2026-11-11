from openai import APIError, APITimeoutError, AsyncOpenAI

from app.ai.capabilities.embeddings import (
    EmbeddingError,
    EmbeddingPurpose,
    EmbeddingResult,
)

MAX_BATCH_SIZE = 256


class OpenAIEmbeddingProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
    ) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    @property
    def model_id(self) -> str:
        return f"openai:{self.model}"

    async def embed(
        self,
        texts: list[str],
        purpose: EmbeddingPurpose,
    ) -> EmbeddingResult:
        # OpenAI embeddings are symmetric, so purpose does not change the call.
        del purpose

        if not texts:
            return EmbeddingResult(vectors=[], model=self.model_id)

        vectors: list[list[float]] = []

        try:
            for start in range(0, len(texts), MAX_BATCH_SIZE):
                batch = texts[start : start + MAX_BATCH_SIZE]

                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )

                ordered = sorted(response.data, key=lambda item: item.index)
                vectors.extend(list(item.embedding) for item in ordered)

        except (APIError, APITimeoutError) as error:
            raise EmbeddingError("Embedding provider unavailable") from error

        if len(vectors) != len(texts):
            raise EmbeddingError("Embedding provider returned an unexpected number of vectors")

        return EmbeddingResult(vectors=vectors, model=self.model_id)
