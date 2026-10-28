from app.ai.capabilities.types import AICapability
from app.services.capability_intent import CapabilityIntent
from app.services.conversation_context_snapshot import (
    ConversationContextSnapshot,
)
from app.services.conversation_source import ConversationSourceResolver


class ConversationSnapshotBuilder:
    def __init__(
        self,
        source_resolver: ConversationSourceResolver | None = None,
    ) -> None:
        self.source_resolver = source_resolver or ConversationSourceResolver()

    def build(
        self,
        message: str,
        intent: CapabilityIntent,
    ) -> ConversationContextSnapshot | None:
        if intent.capability not in {
            AICapability.MESSAGE_EXPLANATION,
            AICapability.TASK_ASSISTANCE,
        }:
            return None

        source = self.source_resolver.resolve(
            message=message,
            source_text=intent.source_text,
        )

        if source is None:
            return None

        return ConversationContextSnapshot(
            capability=intent.capability,
            source=source,
        )
