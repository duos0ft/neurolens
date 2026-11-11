import uuid
from collections.abc import AsyncIterator
from datetime import date

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.providers.local_embeddings import HashingEmbeddingProvider
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.services.knowledge_documents import parse_knowledge_document
from app.services.knowledge_ingestion import IngestionOutcome, KnowledgeIngestionService
from app.services.knowledge_retrieval import DatabaseKnowledgeRetriever


def document_text(
    slug: str,
    body: str,
    *,
    status: str = "verified",
    effective_date: str = "2026-01-01",
) -> str:
    verification = (
        "verified_by: Test Owner\nverified_on: 2025-12-01\n" if status == "verified" else ""
    )

    return (
        f"---\nslug: {slug}\ntitle: Test {slug}\nversion: 1.0\n"
        f"effective_date: {effective_date}\nstatus: {status}\n{verification}---\n\n"
        f"# Test {slug}\n\n## Rules\n\n{body}\n"
    )


@pytest.fixture
async def slug_prefix(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[str]:
    prefix = f"test-{uuid.uuid4().hex[:10]}"

    yield prefix

    async with test_admin_session_factory() as db:
        await db.execute(delete(KnowledgeDocument).where(KnowledgeDocument.slug.startswith(prefix)))
        await db.commit()


async def ingest(
    factory: async_sessionmaker[AsyncSession],
    embedder: HashingEmbeddingProvider,
    raw: str,
):
    async with factory() as db:
        async with db.begin():
            return await KnowledgeIngestionService(db, embedder).ingest(
                parse_knowledge_document(raw, "test.md")
            )


@pytest.mark.asyncio
async def test_ingestion_is_idempotent_and_versions_changes(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    test_session_factory: async_sessionmaker[AsyncSession],
    slug_prefix: str,
) -> None:
    embedder = HashingEmbeddingProvider(dimensions=97)
    slug = f"{slug_prefix}-leave"

    first = await ingest(
        test_admin_session_factory,
        embedder,
        document_text(slug, "Staff may carry over five days of leave."),
    )
    repeat = await ingest(
        test_admin_session_factory,
        embedder,
        document_text(slug, "Staff may carry over five days of leave."),
    )
    revised = await ingest(
        test_admin_session_factory,
        embedder,
        document_text(slug, "Staff may carry over three days of leave."),
    )

    assert (first.outcome, first.revision) == (IngestionOutcome.CREATED, 1)
    assert (repeat.outcome, repeat.revision) == (IngestionOutcome.UNCHANGED, 1)
    assert (revised.outcome, revised.revision) == (IngestionOutcome.REVISED, 2)

    async with test_admin_session_factory() as db:
        revisions = (
            await db.scalars(
                select(KnowledgeDocument)
                .where(KnowledgeDocument.slug == slug)
                .order_by(KnowledgeDocument.revision)
            )
        ).all()

    assert [(doc.revision, doc.is_current) for doc in revisions] == [(1, False), (2, True)]
    assert revisions[0].superseded_at is not None
    assert revisions[1].verified_by == "Test Owner"
    assert revisions[1].source_path == "test.md"

    # The runtime role can read the knowledge base and only sees the
    # current revision.
    async with test_session_factory() as db:
        results = await DatabaseKnowledgeRetriever(db, embedder).retrieve(
            "How many days of leave can staff carry over?", limit=5, min_score=0.0
        )

    assert [result.passage.content for result in results] == [
        "Staff may carry over three days of leave."
    ]
    assert results[0].passage.document_revision == 2


@pytest.mark.asyncio
async def test_retrieval_excludes_drafts_future_and_other_embedding_models(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    test_session_factory: async_sessionmaker[AsyncSession],
    slug_prefix: str,
) -> None:
    embedder = HashingEmbeddingProvider(dimensions=101)

    await ingest(
        test_admin_session_factory,
        embedder,
        document_text(f"{slug_prefix}-draft", "Meal allowance is fifty pounds.", status="draft"),
    )
    await ingest(
        test_admin_session_factory,
        embedder,
        document_text(
            f"{slug_prefix}-future", "Meal allowance is sixty pounds.", effective_date="2099-01-01"
        ),
    )
    await ingest(
        test_admin_session_factory,
        embedder,
        document_text(f"{slug_prefix}-live", "Meal allowance is forty pounds."),
    )

    async with test_session_factory() as db:
        results = await DatabaseKnowledgeRetriever(
            db, embedder, today=lambda: date(2026, 6, 1)
        ).retrieve("What is the meal allowance?", limit=5, min_score=0.0)

        other_model = await DatabaseKnowledgeRetriever(
            db, HashingEmbeddingProvider(dimensions=103)
        ).retrieve("What is the meal allowance?", limit=5, min_score=0.0)

    assert [result.passage.document_slug for result in results] == [f"{slug_prefix}-live"]
    assert other_model == []


@pytest.mark.asyncio
async def test_switching_embedding_model_reembeds_without_new_revision(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    slug_prefix: str,
) -> None:
    slug = f"{slug_prefix}-switch"
    raw = document_text(slug, "Report lost laptops within 24 hours.")

    await ingest(test_admin_session_factory, HashingEmbeddingProvider(dimensions=107), raw)
    switched = await ingest(
        test_admin_session_factory, HashingEmbeddingProvider(dimensions=109), raw
    )

    assert (switched.outcome, switched.revision) == (IngestionOutcome.REEMBEDDED, 1)

    async with test_admin_session_factory() as db:
        models = (
            await db.scalars(
                select(KnowledgeChunk.embedding_model)
                .join(KnowledgeDocument)
                .where(KnowledgeDocument.slug == slug)
            )
        ).all()

    assert set(models) == {"local:hashing-v1-109"}


@pytest.mark.asyncio
async def test_retire_missing_stops_serving_removed_documents(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    slug_prefix: str,
) -> None:
    embedder = HashingEmbeddingProvider(dimensions=113)
    kept = f"{slug_prefix}-kept"
    removed = f"{slug_prefix}-removed"

    await ingest(test_admin_session_factory, embedder, document_text(kept, "Kept rule."))
    await ingest(test_admin_session_factory, embedder, document_text(removed, "Removed rule."))

    async with test_admin_session_factory() as db:
        async with db.begin():
            others = set(
                (
                    await db.scalars(
                        select(KnowledgeDocument.slug).where(
                            KnowledgeDocument.is_current.is_(True),
                            KnowledgeDocument.slug != removed,
                        )
                    )
                ).all()
            )

            reports = await KnowledgeIngestionService(db, embedder).retire_missing(others)

    assert [(report.slug, report.outcome) for report in reports] == [
        (removed, IngestionOutcome.RETIRED)
    ]


@pytest.mark.asyncio
async def test_runtime_role_cannot_modify_knowledge_base(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as db:
        with pytest.raises(DBAPIError, match="permission denied"):
            await db.execute(text("DELETE FROM public.knowledge_documents"))
