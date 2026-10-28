from dataclasses import dataclass

from app.ai.capabilities.types import AICapability
from app.services.conversation_source import ConversationSource


SNAPSHOT_VERSION = 1


@dataclass(frozen=True)
class ConversationContextSnapshot:
    capability: AICapability
    source: ConversationSource

    def to_dict(self) -> dict:
        return {
            "version": SNAPSHOT_VERSION,
            "capability": self.capability.value,
            "source": {
                "text": self.source.text,
                "start": self.source.start,
                "end": self.source.end,
            },
        }

    @classmethod
    def from_dict(
        cls,
        value: dict,
    ) -> "ConversationContextSnapshot":
        if not isinstance(value, dict):
            raise ValueError("Invalid context snapshot")

        if type(value.get("version")) is not int or value["version"] != SNAPSHOT_VERSION:
            raise ValueError("Unsupported context snapshot version")

        raw_source = value.get("source")

        if not isinstance(raw_source, dict):
            raise ValueError("Invalid source data")

        text = raw_source.get("text")
        start = raw_source.get("start")
        end = raw_source.get("end")

        if (
            not isinstance(text, str)
            or not text
            or type(start) is not int
            or type(end) is not int
            or start < 0
            or end <= start
            or end - start != len(text)
        ):
            raise ValueError("Invalid source span")

        try:
            capability = AICapability(value["capability"])
        except (KeyError, ValueError, TypeError) as error:
            raise ValueError("Invalid snapshot capability") from error

        if capability not in {
            AICapability.MESSAGE_EXPLANATION,
            AICapability.TASK_ASSISTANCE,
        }:
            raise ValueError("Unsupported snapshot capability")

        return cls(
            capability=capability,
            source=ConversationSource(
                text=text,
                start=start,
                end=end,
            ),
        )
