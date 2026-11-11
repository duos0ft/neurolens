import uuid
from datetime import date
from pathlib import Path

from app.ai.capabilities.knowledge_retrieval import KnowledgePassage, RetrievedPassage
from app.ai.providers.local_embeddings import HashingEmbeddingProvider
from app.services.knowledge_documents import (
    chunk_knowledge_document,
    embedding_text,
    parse_knowledge_document,
)
from app.services.knowledge_retrieval import InMemoryKnowledgeRetriever

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "resources" / "knowledge" / "duosoft"

CARRY_OVER_TEXT = (
    "Employees may carry over up to five days of unused annual leave into the "
    "next leave year.\n\nCarried-over leave must be used by 31 March of the "
    "following leave year. Any carried-over leave not used by that date is lost."
)


def make_passage(
    content: str = CARRY_OVER_TEXT,
    *,
    slug: str = "annual-leave",
    title: str = "Annual Leave Policy",
    section: str | None = "Carrying over leave",
    source_version: str = "2.1",
    revision: int = 1,
    effective_date: date | None = date(2026, 1, 1),
) -> KnowledgePassage:
    return KnowledgePassage(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_slug=slug,
        document_title=title,
        document_revision=revision,
        source_version=source_version,
        effective_date=effective_date,
        section=section,
        content=content,
        source_path=f"resources/knowledge/duosoft/{slug}.md",
    )


class StaticRetriever:
    """Retriever returning fixed passages, recording each query."""

    def __init__(self, passages: list[KnowledgePassage] | None = None) -> None:
        self.passages = passages or []
        self.queries: list[str] = []

    async def retrieve(
        self,
        query: str,
        *,
        limit: int,
        min_score: float,
    ) -> list[RetrievedPassage]:
        self.queries.append(query)

        return [RetrievedPassage(passage=passage, score=0.9) for passage in self.passages][:limit]


async def build_corpus_retriever(
    include_unverified: bool = False,
) -> InMemoryKnowledgeRetriever:
    """In-memory retriever over the real fictional DuoSoft documents."""

    embedder = HashingEmbeddingProvider()
    items = []

    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        document = parse_knowledge_document(path.read_text(encoding="utf-8"), path.name)

        if not document.is_verified and not include_unverified:
            continue

        chunks = chunk_knowledge_document(document)
        result = await embedder.embed(
            [embedding_text(document.title, chunk) for chunk in chunks],
            purpose="document",
        )

        for chunk, vector in zip(chunks, result.vectors):
            items.append(
                (
                    make_passage(
                        chunk.content,
                        slug=document.slug,
                        title=document.title,
                        section=chunk.section,
                        source_version=document.source_version,
                        effective_date=document.effective_date,
                    ),
                    vector,
                )
            )

    return InMemoryKnowledgeRetriever(embedder, items)
