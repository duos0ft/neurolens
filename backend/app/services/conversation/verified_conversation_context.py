from dataclasses import dataclass

from app.ai.capabilities.types import AICapability
from app.models.conversation_message import ConversationMessage
from app.services.conversation.conversation_capability_metadata import (
    ConversationCapabilityMetadata,
)
from app.services.conversation.conversation_context_snapshot import (
    ConversationContextSnapshot,
)

MAX_VERIFIED_SOURCES = 3

SUPPORTED_CONTEXT_CAPABILITIES = {
    AICapability.MESSAGE_EXPLANATION,
    AICapability.TASK_ASSISTANCE,
}


@dataclass(frozen=True)
class VerifiedConversationContext:
    capability: AICapability
    sources: tuple[str, ...]


class VerifiedConversationContextResolver:
    def resolve(
        self,
        capability: AICapability,
        history: list[ConversationMessage],
    ) -> VerifiedConversationContext:
        empty = VerifiedConversationContext(
            capability=capability,
            sources=(),
        )

        if capability not in SUPPORTED_CONTEXT_CAPABILITIES:
            return empty

        if not history:
            return empty

        sources: list[str] = []

        index = len(history) - 1

        while index >= 1 and len(sources) < MAX_VERIFIED_SOURCES:
            assistant_message = history[index]
            user_message = history[index - 1]

            if user_message.role != "user" or assistant_message.role != "assistant":
                break

            raw_metadata = assistant_message.capability_metadata

            if raw_metadata is None:
                break

            try:
                metadata = ConversationCapabilityMetadata.from_dict(
                    raw_metadata,
                )

            except (
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
            ):
                break

            # Version 1 metadata has no verified source provenance.
            if raw_metadata.get("version") != 2:
                break

            # Never reuse mixed-capability exchanges.
            if metadata.capabilities != (capability,):
                break

            if len(metadata.sources) != 1:
                break

            snapshot: ConversationContextSnapshot = metadata.sources[0]

            if snapshot.capability != capability:
                break

            # The stored offsets must match the original,
            # persisted employee message.
            if not snapshot.source.matches(user_message.content):
                break

            # Recheck the explicit quotation boundary instead of
            # relying only on the previously stored offsets.
            start = snapshot.source.start
            end = snapshot.source.end
            original = user_message.content

            if start == 0 or end >= len(original):
                break

            opening_quote = original[start - 1]
            closing_quote = original[end]

            quote_pairs = {
                '"': '"',
                "“": "”",
                "‘": "’",
            }

            if quote_pairs.get(opening_quote) != closing_quote:
                break

            sources.insert(0, snapshot.source.text)

            index -= 2

        return VerifiedConversationContext(
            capability=capability,
            sources=tuple(sources),
        )
