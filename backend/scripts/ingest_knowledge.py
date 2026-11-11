"""Synchronize organization knowledge documents into the database.

Usage (from the backend directory):

    uv run python -m scripts.ingest_knowledge
    uv run python -m scripts.ingest_knowledge --dry-run
    uv run python -m scripts.ingest_knowledge --source-dir resources/knowledge/duosoft

The application role can only read the knowledge base, so ingestion uses the
privileged MIGRATION_DATABASE_URL connection. The embedding provider comes
from AI_EMBEDDING_PROVIDER and must match the one the API uses at runtime.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.ai.resolver import resolve_embedding_provider
from app.core.settings import settings
from app.services.knowledge_documents import (
    KnowledgeDocumentError,
    ParsedKnowledgeDocument,
    chunk_knowledge_document,
    parse_knowledge_document,
)
from app.services.knowledge_ingestion import KnowledgeIngestionService

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = BACKEND_DIR / "resources" / "knowledge" / "duosoft"


def load_documents(source_dir: Path) -> list[ParsedKnowledgeDocument]:
    paths = sorted(source_dir.glob("*.md"))

    if not paths:
        raise KnowledgeDocumentError(f"No Markdown documents found in {source_dir}")

    documents: list[ParsedKnowledgeDocument] = []
    slugs: set[str] = set()

    for path in paths:
        try:
            relative = path.resolve().relative_to(BACKEND_DIR).as_posix()
        except ValueError:
            relative = path.name

        document = parse_knowledge_document(path.read_text(encoding="utf-8"), relative)

        if document.slug in slugs:
            raise KnowledgeDocumentError(f"Duplicate slug {document.slug!r} in {relative}")

        slugs.add(document.slug)
        documents.append(document)

    return documents


async def ingest(source_dir: Path, *, dry_run: bool, retire_missing: bool) -> int:
    documents = load_documents(source_dir)

    if dry_run:
        for document in documents:
            chunks = chunk_knowledge_document(document)
            print(
                f"{document.slug:<28} {document.verification_status:<9} "
                f"v{document.source_version:<6} {len(chunks):>3} chunks"
            )

        return 0

    if not settings.migration_database_url:
        print("MIGRATION_DATABASE_URL must be configured for ingestion", file=sys.stderr)
        return 1

    embedder = resolve_embedding_provider()
    engine = create_async_engine(settings.migration_database_url)

    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            async with db.begin():
                service = KnowledgeIngestionService(db, embedder)

                reports = [await service.ingest(document) for document in documents]

                if retire_missing:
                    reports.extend(
                        await service.retire_missing({document.slug for document in documents})
                    )

    finally:
        await engine.dispose()

    print(f"Embedding model: {embedder.model_id}")

    for report in reports:
        revision = f"r{report.revision}" if report.revision is not None else "-"
        print(f"{report.slug:<28} {report.outcome.value:<11} {revision:<5} {report.chunk_count:>3}")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and chunk documents without touching the database.",
    )
    parser.add_argument(
        "--keep-missing",
        action="store_true",
        help="Do not retire current documents that are missing from the source folder.",
    )

    args = parser.parse_args()

    try:
        exit_code = asyncio.run(
            ingest(
                args.source_dir,
                dry_run=args.dry_run,
                retire_missing=not args.keep_missing,
            )
        )
    except KnowledgeDocumentError as error:
        print(f"Invalid knowledge document: {error}", file=sys.stderr)
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
