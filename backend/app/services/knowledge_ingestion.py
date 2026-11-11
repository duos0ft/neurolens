import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone
from enum import StrEnum

from sqlalchemy import delete, func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.capabilities.embeddings import EmbeddingError, EmbeddingProvider
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.services.knowledge_documents import (
    DocumentChunk,
    ParsedKnowledgeDocument,
    chunk_knowledge_document,
    embedding_text,
)

logger = logging.getLogger(__name__)


class IngestionOutcome(StrEnum):
    CREATED = "created"
    REVISED = "revised"
    REEMBEDDED = "reembedded"
    UNCHANGED = "unchanged"
    RETIRED = "retired"


@dataclass(frozen=True)
class IngestionReport:
    slug: str
    outcome: IngestionOutcome
    revision: int | None
    chunk_count: int = 0


class KnowledgeIngestionService:
    """Synchronizes knowledge documents into the database.

    Ingestion is idempotent: re-running it with unchanged files does nothing.
    A changed file becomes a new revision and the previous revision is kept
    (no longer current) for provenance.
    """

    def __init__(
        self,
        db: AsyncSession,
        embedder: EmbeddingProvider,
    ) -> None:
        self.db = db
        self.embedder = embedder

    async def _embed_chunks(
        self,
        document: ParsedKnowledgeDocument,
        chunks: list[DocumentChunk],
    ) -> list[KnowledgeChunk]:
        result = await self.embedder.embed(
            [embedding_text(document.title, chunk) for chunk in chunks],
            purpose="document",
        )

        if len(result.vectors) != len(chunks):
            raise EmbeddingError("Embedding count does not match chunk count")

        return [
            KnowledgeChunk(
                chunk_index=chunk.index,
                section=chunk.section,
                content=chunk.content,
                embedding=vector,
                embedding_model=self.embedder.model_id,
                embedding_dimensions=len(vector),
            )
            for chunk, vector in zip(chunks, result.vectors)
        ]

    async def ingest(self, document: ParsedKnowledgeDocument) -> IngestionReport:
        current = await self.db.scalar(
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.slug == document.slug,
                KnowledgeDocument.is_current.is_(True),
            )
            .with_for_update()
        )

        chunks = chunk_knowledge_document(document)

        if current is not None and current.content_sha256 == document.content_sha256:
            embedded_with_current_model = await self.db.scalar(
                select(func.count())
                .select_from(KnowledgeChunk)
                .where(
                    KnowledgeChunk.document_id == current.id,
                    KnowledgeChunk.embedding_model == self.embedder.model_id,
                )
            )

            if embedded_with_current_model:
                return IngestionReport(
                    slug=document.slug,
                    outcome=IngestionOutcome.UNCHANGED,
                    revision=current.revision,
                    chunk_count=embedded_with_current_model,
                )

            # Same content, different embedding model: replace the vectors
            # without creating a new document revision.
            new_chunks = await self._embed_chunks(document, chunks)

            await self.db.execute(
                delete(KnowledgeChunk).where(KnowledgeChunk.document_id == current.id)
            )

            for chunk in new_chunks:
                chunk.document_id = current.id

            self.db.add_all(new_chunks)
            await self.db.flush()

            return IngestionReport(
                slug=document.slug,
                outcome=IngestionOutcome.REEMBEDDED,
                revision=current.revision,
                chunk_count=len(new_chunks),
            )

        # Embed before mutating anything so a provider failure leaves the
        # existing revision untouched.
        new_chunks = await self._embed_chunks(document, chunks)

        latest_revision = await self.db.scalar(
            select(func.max(KnowledgeDocument.revision)).where(
                KnowledgeDocument.slug == document.slug,
            )
        )

        now = datetime.now(timezone.utc)

        if current is not None:
            current.is_current = False
            current.superseded_at = now
            await self.db.flush()

        record = KnowledgeDocument(
            slug=document.slug,
            title=document.title,
            revision=(latest_revision or 0) + 1,
            source_version=document.source_version,
            owner=document.owner,
            effective_date=document.effective_date,
            source_path=document.source_path,
            content_sha256=document.content_sha256,
            verification_status=document.verification_status,
            verified_by=document.verified_by,
            verified_at=(
                datetime.combine(document.verified_on, time.min, tzinfo=timezone.utc)
                if document.verified_on is not None
                else None
            ),
            is_current=True,
        )

        self.db.add(record)
        await self.db.flush()

        for chunk in new_chunks:
            chunk.document_id = record.id

        self.db.add_all(new_chunks)
        await self.db.flush()

        return IngestionReport(
            slug=document.slug,
            outcome=(IngestionOutcome.REVISED if current is not None else IngestionOutcome.CREATED),
            revision=record.revision,
            chunk_count=len(new_chunks),
        )

    async def retire_missing(self, present_slugs: set[str]) -> list[IngestionReport]:
        """Stop serving documents that were removed from the source folder."""

        stale = await self.db.scalars(
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.is_current.is_(True),
                KnowledgeDocument.slug.not_in(present_slugs) if present_slugs else true(),
            )
            .with_for_update()
        )

        now = datetime.now(timezone.utc)
        reports: list[IngestionReport] = []

        for document in stale.all():
            document.is_current = False
            document.superseded_at = now

            reports.append(
                IngestionReport(
                    slug=document.slug,
                    outcome=IngestionOutcome.RETIRED,
                    revision=document.revision,
                )
            )

        await self.db.flush()

        return reports
