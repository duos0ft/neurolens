import math
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import Date, Integer, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.capabilities.embeddings import EmbeddingProvider


@dataclass(frozen=True)
class PolicySearchResult:
    chunk_id: UUID
    document_id: UUID
    version_id: UUID
    document_title: str
    version_number: int
    content: str
    section_title: str | None
    page_number: int | None
    distance: float


class PolicyRetrievalService:
    def __init__(
        self,
        db: AsyncSession,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.db = db
        self.embedding_provider = embedding_provider

    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[PolicySearchResult]:
        normalized_query = query.strip()

        if not normalized_query:
            return []

        if not 1 <= limit <= 20:
            raise ValueError("Search limit must be between 1 and 20")

        embeddings = await self.embedding_provider.embed([normalized_query])

        if len(embeddings) != 1:
            raise ValueError("Expected exactly one query embedding")

        query_embedding = embeddings[0]

        if len(query_embedding) != 1536 or any(
            not math.isfinite(value) for value in query_embedding
        ):
            raise ValueError("Invalid query embedding")

        vector_literal = "[" + ",".join(str(value) for value in query_embedding) + "]"

        statement = text(
            """
            SELECT
                c.id AS chunk_id,
                d.id AS document_id,
                v.id AS version_id,
                d.title AS document_title,
                v.version_number,
                c.content,
                c.section_title,
                c.page_number,
                c.embedding OPERATOR(extensions.<=>)
                CAST(:query_embedding AS extensions.vector(1536))
                    AS distance
            FROM public.policy_chunks AS c
                JOIN public.policy_versions AS v
            ON v.id = c.version_id
                JOIN public.policy_documents AS d
                ON d.id = v.document_id
            WHERE
                v.ingestion_status = 'ready'
              AND v.publication_status = 'published'
              AND (
                v.effective_date IS NULL
               OR v.effective_date <= :effective_date
                )
            ORDER BY distance ASC
                LIMIT :result_limit
            """
        ).bindparams(
            bindparam("effective_date", type_=Date()),
            bindparam("result_limit", type_=Integer()),
        )

        result = await self.db.execute(
            statement,
            {
                "query_embedding": vector_literal,
                "effective_date": date.today(),
                "result_limit": limit,
            },
        )

        rows = result.mappings().all()

        return [
            PolicySearchResult(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                version_id=row["version_id"],
                document_title=row["document_title"],
                version_number=row["version_number"],
                content=row["content"],
                section_title=row["section_title"],
                page_number=row["page_number"],
                distance=float(row["distance"]),
            )
            for row in rows
        ]
