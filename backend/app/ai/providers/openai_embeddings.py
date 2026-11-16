import math

from openai import AsyncOpenAI, OpenAIError

from app.ai.capabilities.embeddings import (
    EmbeddingError,
    EmbeddingProvider,
)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
    ) -> None:
        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=30.0,
            max_retries=2,
        )
        self.model = model
        self.dimensions = dimensions

    async def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        if any(not text.strip() for text in texts):
            raise EmbeddingError("Embedding inputs cannot be empty")

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions,
                encoding_format="float",
            )

        except OpenAIError as error:
            raise EmbeddingError("Unable to generate embeddings") from error

        if len(response.data) != len(texts):
            raise EmbeddingError("Embedding response count does not match input count")

        embeddings: list[list[float] | None] = [None for _ in texts]

        for item in response.data:
            if (
                type(item.index) is not int
                or item.index < 0
                or item.index >= len(texts)
                or embeddings[item.index] is not None
            ):
                raise EmbeddingError("Invalid embedding response index")

            vector = item.embedding

            if len(vector) != self.dimensions or not all(math.isfinite(value) for value in vector):
                raise EmbeddingError("Invalid embedding vector")

            embeddings[item.index] = vector

        if any(vector is None for vector in embeddings):
            raise EmbeddingError("Embedding response is incomplete")

        return [vector for vector in embeddings if vector is not None]
