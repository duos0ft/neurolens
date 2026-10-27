from dataclasses import dataclass

from app.ai.capabilities.text_generation import GenerationMessage
from app.ai.capabilities.types import AICapability
from app.models.conversation_message import ConversationMessage
from app.services.conversation_capability_metadata import (
    ConversationCapabilityMetadata,
)


MAX_CAPABILITY_TURNS = 3


@dataclass(frozen=True)
class CapabilityHistory:
    capability: AICapability
    messages: list[GenerationMessage]


class CapabilityHistoryResolver:
    def resolve(
        self,
        capability: AICapability,
        history: list[ConversationMessage],
    ) -> CapabilityHistory:
        if capability == AICapability.POLICY_QUESTION:
            return CapabilityHistory(
                capability=capability,
                messages=[],
            )

        if not history:
            return CapabilityHistory(
                capability=capability,
                messages=[],
            )

        messages: list[GenerationMessage] = []

        # Work backwards through complete user/assistant exchanges.
        index = len(history) - 1

        while index >= 1 and len(messages) < MAX_CAPABILITY_TURNS * 2:
            assistant_message = history[index]
            user_message = history[index - 1]

            if (
                user_message.role != "user"
                or assistant_message.role != "assistant"
                or assistant_message.capability_metadata is None
            ):
                break

            try:
                metadata = ConversationCapabilityMetadata.from_dict(
                    assistant_message.capability_metadata,
                )
            except (ValueError, TypeError, KeyError, AttributeError):
                break

            # A mixed-capability response cannot be safely assigned
            # to one specialist provider.
            if metadata.capabilities != (capability,):
                break

            messages[0:0] = [
                GenerationMessage(
                    role="user",
                    content=user_message.content,
                ),
                GenerationMessage(
                    role="assistant",
                    content=assistant_message.content,
                ),
            ]

            index -= 2

        return CapabilityHistory(
            capability=capability,
            messages=messages,
        )
