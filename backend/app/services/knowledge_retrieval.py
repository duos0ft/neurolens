import heapq
import math
from collections.abc import Callable, Sequence
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.capabilities.embeddings import EmbeddingError, EmbeddingProvider
from app.ai.capabilities.knowledge_retrieval import KnowledgePassage, RetrievedPassage
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Vectors must have the same dimensions")

    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0

    for a, b in zip(left, right):
        dot += a * b
        left_norm += a * a
        right_norm += b * b

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot / (math.sqrt(left_norm) * math.sqrt(right_norm))


def rank_passages(
    query_vector: Sequence[float],
    candidates: Sequence[tuple[KnowledgePassage, Sequence[float]]],
    *,
    limit: int,
    min_score: float,
) -> list[RetrievedPassage]:
    scored = (
        RetrievedPassage(passage=passage, score=cosine_similarity(query_vector, vector))
        for passage, vector in candidates
        if len(vector) == len(query_vector)
    )

    relevant = [result for result in scored if result.score >= min_score]

    return heapq.nlargest(limit, relevant, key=lambda result: result.score)


async def _embed_query(embedder: EmbeddingProvider, query: str) -> list[float]:
    result = await embedder.embed([query], purpose="query")

    if len(result.vectors) != 1:
        raise EmbeddingError("Embedding provider returned an unexpected number of vectors")

    return result.vectors[0]


class DatabaseKnowledgeRetriever:
    """Retrieves verified, current passages stored in PostgreSQL.

    Similarity is computed in Python. That is appropriate for the PoC's
    small policy corpus and keeps the schema portable. A pgvector-backed
    retriever can implement the same protocol when the corpus grows.
    """

    def __init__(
        self,
        db: AsyncSession,
        embedder: EmbeddingProvider,
        today: Callable[[], date] = date.today,
    ) -> None:
        self.db = db
        self.embedder = embedder
        self.today = today

    async def retrieve(
        self,
        query: str,
        *,
        limit: int,
        min_score: float,
    ) -> list[RetrievedPassage]:
        query = query.strip()

        if not query or limit <= 0:
            return []

        rows = await self.db.execute(
            select(KnowledgeChunk, KnowledgeDocument)
            .join(
                KnowledgeDocument,
                KnowledgeDocument.id == KnowledgeChunk.document_id,
            )
            .where(
                KnowledgeDocument.is_current.is_(True),
                KnowledgeDocument.verification_status == "verified",
                or_(
                    KnowledgeDocument.effective_date.is_(None),
                    KnowledgeDocument.effective_date <= self.today(),
                ),
                KnowledgeChunk.embedding_model == self.embedder.model_id,
            )
        )

        candidates = [
            (
                KnowledgePassage(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    document_slug=document.slug,
                    document_title=document.title,
                    document_revision=document.revision,
                    source_version=document.source_version,
                    effective_date=document.effective_date,
                    section=chunk.section,
                    content=chunk.content,
                    source_path=document.source_path,
                ),
                chunk.embedding,
            )
            for chunk, document in rows.all()
        ]

        if not candidates:
            return []

        query_vector = await _embed_query(self.embedder, query)

        return rank_passages(
            query_vector,
            candidates,
            limit=limit,
            min_score=min_score,
        )


class InMemoryKnowledgeRetriever:
    """Retriever over pre-embedded passages held in memory.

    Used by tests and offline evaluation. Callers are responsible for only
    adding verified passages.
    """

    def __init__(
        self,
        embedder: EmbeddingProvider,
        passages: Sequence[tuple[KnowledgePassage, Sequence[float]]] = (),
    ) -> None:
        self.embedder = embedder
        self.passages = list(passages)

    async def retrieve(
        self,
        query: str,
        *,
        limit: int,
        min_score: float,
    ) -> list[RetrievedPassage]:
        query = query.strip()

        if not query or limit <= 0 or not self.passages:
            return []

        query_vector = await _embed_query(self.embedder, query)

        return rank_passages(
            query_vector,
            self.passages,
            limit=limit,
            min_score=min_score,
        )
