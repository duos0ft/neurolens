from dataclasses import dataclass

from app.services.policy.policy_retrieval import PolicySearchResult


@dataclass(frozen=True)
class PolicyCitation:
    reference: str
    document_id: str
    version_id: str
    document_title: str
    version_number: int
    page_number: int | None
    chunk_id: str


@dataclass(frozen=True)
class PolicyContext:
    text: str
    citations: list[PolicyCitation]


class PolicyContextService:
    def build(
        self,
        results: list[PolicySearchResult],
    ) -> PolicyContext:
        passages: list[str] = []
        citations: list[PolicyCitation] = []

        seen_chunks: set[str] = set()

        for result in results:
            chunk_id = str(result.chunk_id)

            if chunk_id in seen_chunks:
                continue

            seen_chunks.add(chunk_id)

            reference = f"P{len(citations) + 1}"

            citations.append(
                PolicyCitation(
                    reference=reference,
                    document_id=str(result.document_id),
                    version_id=str(result.version_id),
                    document_title=result.document_title,
                    version_number=result.version_number,
                    page_number=result.page_number,
                    chunk_id=chunk_id,
                )
            )

            location = (
                f"Page {result.page_number}"
                if result.page_number is not None
                else "Page unavailable"
            )

            section = f"\nSection: {result.section_title}" if result.section_title else ""

            passages.append(
                f"[{reference}]\n"
                f"Document: {result.document_title}\n"
                f"Version: {result.version_number}\n"
                f"{location}"
                f"{section}\n"
                f"Content:\n{result.content}"
            )

        return PolicyContext(
            text="\n\n---\n\n".join(passages),
            citations=citations,
        )
