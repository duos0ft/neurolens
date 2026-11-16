from app.ai.capabilities.embeddings import EmbeddingProvider
from app.ai.providers.openai_embeddings import OpenAIEmbeddingProvider
from app.core.settings import settings


def create_embedding_provider() -> EmbeddingProvider:
    if settings.ai_embedding_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required for embedding generation")

        if settings.ai_embedding_dimensions != 1536:
            raise ValueError("Policy embeddings must match the configured pgvector dimensions")

        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
            dimensions=settings.ai_embedding_dimensions,
        )

    raise ValueError(f"Unsupported embedding provider: {settings.ai_embedding_provider}")
