import pytest

from app.ai.capabilities.types import AICapability
from app.ai.providers.openai import OpenAITextGenerationProvider
from app.ai.resolver import (
    resolve_ai_provider_registry,
    resolve_text_generation_provider,
)
from app.core.settings import settings


def test_resolves_default_text_generation_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_text_generation_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-api-key")

    provider = resolve_text_generation_provider()

    assert isinstance(provider, OpenAITextGenerationProvider)


def test_registers_separate_capability_providers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_text_generation_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-api-key")

    registry = resolve_ai_provider_registry()

    explanation_provider = registry.get_text_generation(
        AICapability.MESSAGE_EXPLANATION,
    )

    task_provider = registry.get_text_generation(
        AICapability.TASK_ASSISTANCE,
    )

    title_provider = registry.get_text_generation(
        AICapability.CONVERSATION_TITLE,
    )

    assert isinstance(explanation_provider, OpenAITextGenerationProvider)
    assert isinstance(task_provider, OpenAITextGenerationProvider)
    assert isinstance(title_provider, OpenAITextGenerationProvider)

    assert explanation_provider is not task_provider
    assert task_provider is not title_provider


def test_missing_openai_api_key_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_text_generation_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", None)

    with pytest.raises(RuntimeError, match="OpenAI API key"):
        resolve_ai_provider_registry()


def test_unsupported_provider_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_text_generation_provider", "unsupported")

    with pytest.raises(ValueError, match="Unsupported text generation provider"):
        resolve_ai_provider_registry()
