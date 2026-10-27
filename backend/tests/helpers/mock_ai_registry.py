import json

from app.ai.capabilities.types import AICapability
from app.ai.registry import AIProviderRegistry
from tests.helpers.mock_ai_provider import MockAIProvider


def create_mock_ai_registry() -> tuple[
    AIProviderRegistry,
    dict[AICapability, MockAIProvider],
]:
    registry = AIProviderRegistry()

    providers = {
        AICapability.REQUEST_CLASSIFICATION: MockAIProvider(
            json.dumps(
                {
                    "intents": [
                        {
                            "capability": "message_explanation",
                            "instruction": "Explain the employee's message.",
                            "source_text": None,
                        }
                    ]
                }
            )
        ),
        AICapability.MESSAGE_EXPLANATION: MockAIProvider("Your manager is requesting an update."),
        AICapability.TASK_ASSISTANCE: MockAIProvider("1. Review progress.\n2. Report blockers."),
        AICapability.GENERAL_CONVERSATION: MockAIProvider("How can I help you today?"),
        AICapability.CONVERSATION_TITLE: MockAIProvider("Understanding Workplace Messages"),
    }

    for capability, provider in providers.items():
        registry.register_text_generation(
            capability,
            provider,
        )

    return registry, providers