from app.ai.capabilities.embeddings import EmbeddingProvider
from app.ai.capabilities.text_generation import TextGenerationProvider
from app.ai.capabilities.types import AICapability
from app.ai.providers.local_embeddings import HashingEmbeddingProvider
from app.ai.providers.openai import OpenAITextGenerationProvider
from app.ai.providers.openai_embeddings import OpenAIEmbeddingProvider
from app.ai.registry import AIProviderRegistry
from app.core.settings import settings


def resolve_text_generation_provider(
    model: str | None = None,
) -> TextGenerationProvider:
    if settings.ai_text_generation_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OpenAI API key is not configured")

        return OpenAITextGenerationProvider(
            api_key=settings.openai_api_key,
            model=model or settings.openai_text_generation_model,
        )

    raise ValueError(
        f"Unsupported text generation provider: {settings.ai_text_generation_provider}"
    )


def resolve_embedding_provider() -> EmbeddingProvider:
    if settings.ai_embedding_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OpenAI API key is not configured")

        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        )

    if settings.ai_embedding_provider == "local":
        return HashingEmbeddingProvider()

    raise ValueError(f"Unsupported embedding provider: {settings.ai_embedding_provider}")


def resolve_ai_provider_registry() -> AIProviderRegistry:
    registry = AIProviderRegistry()

    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION,
        resolve_text_generation_provider(
            settings.ai_request_classification_model,
        ),
    )

    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        resolve_text_generation_provider(
            settings.ai_message_explanation_model,
        ),
    )

    registry.register_text_generation(
        AICapability.TASK_ASSISTANCE,
        resolve_text_generation_provider(
            settings.ai_task_assistance_model,
        ),
    )

    registry.register_text_generation(
        AICapability.TASK_EXTRACTION,
        resolve_text_generation_provider(
            settings.ai_task_assistance_model,
        ),
    )

    registry.register_text_generation(
        AICapability.CONVERSATION_TITLE,
        resolve_text_generation_provider(
            settings.ai_conversation_title_model,
        ),
    )

    registry.register_text_generation(
        AICapability.GENERAL_CONVERSATION,
        resolve_text_generation_provider(),
    )

    registry.register_text_generation(
        AICapability.POLICY_GENERATION,
        resolve_text_generation_provider(
            settings.ai_policy_generation_model,
        ),
    )

    registry.register_embeddings(
        resolve_embedding_provider(),
    )

    return registry
