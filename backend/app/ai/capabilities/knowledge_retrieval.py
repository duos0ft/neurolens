import uuid
from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class KnowledgePassage:
    """A verified chunk of an organization document plus its provenance."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_slug: str
    document_title: str
    document_revision: int
    source_version: str
    effective_date: date | None
    section: str | None
    content: str
    source_path: str


@dataclass(frozen=True)
class RetrievedPassage:
    passage: KnowledgePassage
    score: float


class KnowledgeRetriever(Protocol):
    """Returns the most relevant verified passages for a query.

    Implementations must only return passages from documents that are
    verified and current. Callers rely on this to ground policy answers.
    """

    async def retrieve(
        self,
        query: str,
        *,
        limit: int,
        min_score: float,
    ) -> list[RetrievedPassage]: ...
