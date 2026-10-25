import json
from dataclasses import dataclass

from app.ai.capabilities.text_generation import (
    GenerationMessage,
    TextGenerationProvider,
    TextGenerationRequest,
)
from app.ai.capabilities.types import AICapability


CLASSIFICATION_INSTRUCTIONS = """
Classify employee requests for NeuroLens.

Return every applicable intent.

Available intents:
- general_conversation: Greetings, ordinary conversation, or
  general questions that do not require specialized assistance.
- message_explanation: Explain workplace messages, jargon,
  indirect language, or ambiguous communication.
- task_assistance: Break down work, create action lists,
  prioritize assignments, or plan tasks.
- policy_question: Questions requiring the organization's
  actual policies, entitlements, benefits, rules, or procedures.

A request can contain multiple intents.

Examples:
"Hello."
["general_conversation"]

"Explain what my manager meant."
["message_explanation"]

"Break this task into steps."
["task_assistance"]

"Explain this message and make me a checklist."
["message_explanation", "task_assistance"]

"How many annual leave days am I entitled to?"
["policy_question"]

"Explain this HR message and tell me our leave policy."
["message_explanation", "policy_question"]

Do not answer the employee.
Return only a JSON array of intent identifiers.
"""


@dataclass(frozen=True)
class CapabilityClassification:
    capabilities: list[AICapability]


class CapabilityClassifier:
    def __init__(
        self,
        provider: TextGenerationProvider,
    ) -> None:
        self.provider = provider

    async def classify(
        self,
        message: str,
    ) -> CapabilityClassification:
        if not message.strip():
            raise ValueError("Message cannot be empty")

        request = TextGenerationRequest(
            system_instructions=CLASSIFICATION_INSTRUCTIONS,
            messages=[
                GenerationMessage(
                    role="user",
                    content=message.strip(),
                ),
            ],
        )

        response = await self.provider.generate(request)

        try:
            values = json.loads(response.content)

            if not isinstance(values, list):
                raise ValueError("Classification must be a JSON array")

            capabilities = []

            for value in values:
                capability = AICapability(value)

                if capability not in {
                    AICapability.GENERAL_CONVERSATION,
                    AICapability.MESSAGE_EXPLANATION,
                    AICapability.TASK_ASSISTANCE,
                    AICapability.POLICY_QUESTION,
                }:
                    raise ValueError("Unsupported classification capability")

                if capability not in capabilities:
                    capabilities.append(capability)

        except (ValueError, TypeError) as error:
            raise ValueError("Unable to interpret capability classification") from error

        return CapabilityClassification(
            capabilities=capabilities,
        )