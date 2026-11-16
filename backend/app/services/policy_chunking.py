from dataclasses import dataclass

import tiktoken

from app.services.policy_text_extraction import ExtractedPolicyPage


@dataclass(frozen=True)
class ExtractedPolicyChunk:
    chunk_index: int
    content: str
    section_title: str | None
    page_number: int
    token_count: int


class PolicyChunkingService:
    def __init__(
        self,
        chunk_size: int = 400,
        chunk_overlap: int = 60,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")

        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("Invalid chunk overlap")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def chunk(
        self,
        pages: list[ExtractedPolicyPage],
    ) -> list[ExtractedPolicyChunk]:
        chunks: list[ExtractedPolicyChunk] = []

        for page in pages:
            tokens = self.encoding.encode(page.content)

            if not tokens:
                continue

            start = 0

            while start < len(tokens):
                end = min(
                    start + self.chunk_size,
                    len(tokens),
                )

                content = self.encoding.decode(tokens[start:end]).strip()

                if content:
                    chunks.append(
                        ExtractedPolicyChunk(
                            chunk_index=len(chunks),
                            content=content,
                            section_title=None,
                            page_number=page.page_number,
                            token_count=len(self.encoding.encode(content)),
                        )
                    )

                if end == len(tokens):
                    break

                start = end - self.chunk_overlap

        return chunks
