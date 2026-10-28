from dataclasses import dataclass

QUOTE_PAIRS = {
    '"': '"',
    "“": "”",
    "‘": "’",
}


@dataclass(frozen=True)
class ConversationSource:
    text: str
    start: int
    end: int

    def matches(self, original_message: str) -> bool:
        return (
            0 <= self.start < self.end <= len(original_message)
            and original_message[self.start : self.end] == self.text
        )


class ConversationSourceResolver:
    def resolve(
        self,
        message: str,
        source_text: str | None,
    ) -> ConversationSource | None:
        if not message or not source_text:
            return None

        # An exact substring match is necessary but not sufficient.
        # Require the source to be explicitly delimited by quotes.
        for opening, closing in QUOTE_PAIRS.items():
            search_start = 0

            while search_start < len(message):
                opening_index = message.find(
                    opening,
                    search_start,
                )

                if opening_index == -1:
                    break

                content_start = opening_index + len(opening)

                closing_index = message.find(
                    closing,
                    content_start,
                )

                if closing_index == -1:
                    break

                quoted_text = message[content_start:closing_index]

                if quoted_text == source_text:
                    return ConversationSource(
                        text=source_text,
                        start=content_start,
                        end=closing_index,
                    )

                search_start = closing_index + len(closing)

        return None
