import pytest

from app.ai.capabilities.types import AICapability
from app.ai.registry import (
    AIProviderRegistry,
    ProviderNotConfiguredError,
)
from tests.test_assistant_orchestrator import MockProvider


def test_registers_provider_for_capability() -> None:
    registry = AIProviderRegistry()
    provider = object()

    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        provider,
    )

    assert (
        registry.get_text_generation(
            AICapability.MESSAGE_EXPLANATION,
        )
        is provider
    )


def test_supports_different_providers() -> None:
    registry = AIProviderRegistry()

    explanation_provider = object()
    task_provider = object()

    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        explanation_provider,
    )

    registry.register_text_generation(
        AICapability.TASK_ASSISTANCE,
        task_provider,
    )

    assert (
        registry.get_text_generation(
            AICapability.MESSAGE_EXPLANATION,
        )
        is explanation_provider
    )

    assert (
        registry.get_text_generation(
            AICapability.TASK_ASSISTANCE,
        )
        is task_provider
    )


def test_missing_provider_raises_error() -> None:
    registry = AIProviderRegistry()

    with pytest.raises(ProviderNotConfiguredError):
        registry.get_text_generation(
            AICapability.CONVERSATION_TITLE,
        )


def test_rejects_unsupported_capability() -> None:
    registry = AIProviderRegistry()

    with pytest.raises(ValueError):
        registry.register_text_generation(
            AICapability.EMBEDDINGS,
            object(),
        )


def test_registry_supports_task_extraction() -> None:
    registry = AIProviderRegistry()
    provider = MockProvider('{"tasks": []}')

    registry.register_text_generation(
        AICapability.TASK_EXTRACTION,
        provider,
    )

    assert registry.get_text_generation(AICapability.TASK_EXTRACTION) is provider
