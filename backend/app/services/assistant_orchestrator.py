from dataclasses import dataclass

from app.ai.capabilities.text_generation import (
    GenerationMessage,
    TextGenerationRequest,
    TextGenerationResponse,
    TextGenerationError,
)
from app.ai.capabilities.types import AICapability
from app.ai.registry import AIProviderRegistry, ProviderNotConfiguredError
from app.services.capability_classifier import CapabilityClassifier

EXPLANATION_INSTRUCTIONS = """
You are NeuroLens, a workplace communication assistant.

Explain workplace messages clearly and respectfully.
Distinguish explicit instructions from possible interpretations.
Explain jargon and ambiguous wording when relevant.
Do not invent intentions, company policies, deadlines, or facts.
Do not generate a detailed task execution plan.
"""

TASK_INSTRUCTIONS = """
You are NeuroLens, a workplace task-assistance specialist.

Identify actionable work supported by the employee's message.
Break tasks into clear, manageable steps.
Separate confirmed requirements from assumptions.
Highlight missing information when it affects execution.
Do not invent company policies, deadlines, or responsibilities.
"""


@dataclass(frozen=True)
class CapabilityResult:
    capability: AICapability
    response: TextGenerationResponse


class CapabilityDisabledError(Exception):
    pass


class AssistantOrchestrator:
    def __init__(
        self,
        registry: AIProviderRegistry,
        enable_task_assistance: bool = True,
    ) -> None:
        self.registry = registry
        self.enable_task_assistance = enable_task_assistance

    async def execute(
        self,
        message: str,
        capabilities: list[AICapability],
        history: list[GenerationMessage] | None = None,
    ) -> list[CapabilityResult]:
        if not message.strip():
            raise ValueError("Message cannot be empty")

        if not capabilities:
            raise ValueError("At least one capability is required")

        selected = list(dict.fromkeys(capabilities))

        supported = {
            AICapability.MESSAGE_EXPLANATION,
            AICapability.TASK_ASSISTANCE,
        }

        for capability in selected:
            if capability not in supported:
                raise ValueError(f"Unsupported assistant capability: {capability.value}")

            if capability == AICapability.TASK_ASSISTANCE and not self.enable_task_assistance:
                raise CapabilityDisabledError("Task assistance is disabled")

        instructions = {
            AICapability.MESSAGE_EXPLANATION: EXPLANATION_INSTRUCTIONS,
            AICapability.TASK_ASSISTANCE: TASK_INSTRUCTIONS,
        }

        results = []

        for capability in selected:
            provider = self.registry.get_text_generation(capability)

            request = TextGenerationRequest(
                system_instructions=instructions[capability],
                messages=[
                    *(history or []),
                    GenerationMessage(
                        role="user",
                        content=message.strip(),
                    ),
                ],
            )

            response = await provider.generate(request)

            results.append(
                CapabilityResult(
                    capability=capability,
                    response=response,
                )
            )

        return results

    async def respond(
        self,
        message: str,
        history: list[GenerationMessage] | None = None,
    ) -> list[CapabilityResult]:
        if not message.strip():
            raise ValueError("Message cannot be empty")

        try:
            provider = self.registry.get_text_generation(
                AICapability.REQUEST_CLASSIFICATION,
            )

            classifier = CapabilityClassifier(provider)
            classification = await classifier.classify(message)

        except (ValueError, TextGenerationError, ProviderNotConfiguredError):
            return []

        permitted_capabilities = [
            capability
            for capability in classification.capabilities
            if (capability != AICapability.TASK_ASSISTANCE or self.enable_task_assistance)
        ]

        if not permitted_capabilities:
            return []

        return await self.execute(
            message=message,
            capabilities=permitted_capabilities,
            history=history,
        )