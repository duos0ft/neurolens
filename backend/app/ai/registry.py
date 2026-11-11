from app.ai.capabilities.text_generation import TextGenerationProvider
from app.ai.capabilities.types import AICapability

TEXT_GENERATION_CAPABILITIES = frozenset(
    {
        AICapability.REQUEST_CLASSIFICATION,
        AICapability.MESSAGE_EXPLANATION,
        AICapability.TASK_ASSISTANCE,
        AICapability.TASK_EXTRACTION,
        AICapability.CALENDAR_EXTRACTION,
        AICapability.POLICY_GENERATION,
        AICapability.CONVERSATION_TITLE,
        AICapability.GENERAL_CONVERSATION,
    }
)


class ProviderNotConfiguredError(Exception):
    pass


class AIProviderRegistry:
    def __init__(self) -> None:
        self._text_generation_providers: dict[
            AICapability,
            TextGenerationProvider,
        ] = {}

    def register_text_generation(
        self,
        capability: AICapability,
        provider: TextGenerationProvider,
    ) -> None:
        if capability not in TEXT_GENERATION_CAPABILITIES:
            raise ValueError(f"{capability.value} is not a text-generation capability")

        self._text_generation_providers[capability] = provider

    def get_text_generation(
        self,
        capability: AICapability,
    ) -> TextGenerationProvider:
        if capability not in TEXT_GENERATION_CAPABILITIES:
            raise ValueError(f"{capability.value} is not a text-generation capability")

        provider = self._text_generation_providers.get(capability)

        if provider is None:
            raise ProviderNotConfiguredError(
                f"No text-generation provider configured for {capability.value}"
            )

        return provider
