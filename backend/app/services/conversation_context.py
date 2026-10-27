from dataclasses import dataclass

from app.ai.capabilities.text_generation import GenerationMessage
from app.ai.capabilities.types import AICapability


MAX_CONTEXT_MESSAGES = 10


@dataclass(frozen=True)
class ConversationContext:
    messages: list[GenerationMessage]


class ConversationContextResolver:
    def resolve(
        self,
        capability: AICapability,
        history: list[GenerationMessage] | None = None,
        has_policy_question: bool = False,
        has_isolated_source: bool = False,
        trusted_context: bool = False,
    ) -> ConversationContext:
        if not history:
            return ConversationContext(messages=[])

        if has_policy_question or has_isolated_source:
            return ConversationContext(messages=[])

        if capability == AICapability.GENERAL_CONVERSATION:
            # General conversation may use recent turns when the
            # caller has explicitly approved their use.
            if trusted_context:
                return ConversationContext(
                    messages=list(history[-MAX_CONTEXT_MESSAGES:]),
                )

            return ConversationContext(messages=[])

        # Specialized models do not receive previous messages
        # until their capability ownership can be verified.
        return ConversationContext(messages=[])
