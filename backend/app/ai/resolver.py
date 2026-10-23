from app.ai.capabilities.text_generation import TextGenerationProvider
from app.ai.providers.openai import OpenAITextGenerationProvider
from app.core.settings import settings


def resolve_text_generation_provider() -> TextGenerationProvider:
    if settings.ai_text_generation_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OpenAI API key is not configured")

        return OpenAITextGenerationProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_text_generation_model,
        )

    raise ValueError(
        f"Unsupported text generation provider: {settings.ai_text_generation_provider}"
    )
