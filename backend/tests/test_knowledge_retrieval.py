import math

import pytest

from app.ai.providers.local_embeddings import HashingEmbeddingProvider
from app.services.knowledge_retrieval import (
    InMemoryKnowledgeRetriever,
    cosine_similarity,
    rank_passages,
)
from tests.helpers.knowledge import build_corpus_retriever, make_passage


@pytest.mark.asyncio
async def test_hashing_embeddings_are_deterministic_and_normalized() -> None:
    provider = HashingEmbeddingProvider(dimensions=64)

    first = await provider.embed(["Annual leave carry over"], purpose="document")
    second = await provider.embed(["Annual leave carry over"], purpose="query")

    assert first.vectors == second.vectors
    assert first.model == "local:hashing-v1-64"
    assert math.isclose(sum(value * value for value in first.vectors[0]), 1.0)


@pytest.mark.asyncio
async def test_hashing_embedding_of_stop_words_only_is_zero() -> None:
    provider = HashingEmbeddingProvider(dimensions=32)

    result = await provider.embed(["the and of"], purpose="query")

    assert result.vectors[0] == [0.0] * 32


def test_cosine_similarity() -> None:
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine_similarity([0, 0], [1, 0]) == 0.0

    with pytest.raises(ValueError):
        cosine_similarity([1, 0], [1, 0, 0])


def test_rank_passages_applies_threshold_limit_and_skips_other_dimensions() -> None:
    near = make_passage("near")
    far = make_passage("far")
    other_space = make_passage("other")

    results = rank_passages(
        [1.0, 0.0],
        [(far, [0.0, 1.0]), (near, [0.9, 0.1]), (other_space, [1.0, 0.0, 0.0])],
        limit=5,
        min_score=0.5,
    )

    assert [result.passage for result in results] == [near]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("question", "slug", "section"),
    [
        ("How many days of annual leave do I get?", "annual-leave", "Entitlement"),
        ("Can I carry over unused leave?", "annual-leave", "Carrying over leave"),
        ("Can I work from home three days a week?", "remote-work", "Hybrid working pattern"),
        ("Do I need a diagnosis to ask for an adjustment?", "employee-support", None),
        ("How fast should I reply to emails?", "communication-guidelines", "Response times"),
    ],
)
async def test_corpus_retrieval_ranks_relevant_section_first(
    question: str,
    slug: str,
    section: str | None,
) -> None:
    retriever = await build_corpus_retriever()

    results = await retriever.retrieve(question, limit=3, min_score=0.1)

    assert results
    assert results[0].passage.document_slug == slug

    if section is not None:
        assert results[0].passage.section == section


@pytest.mark.asyncio
async def test_unrelated_question_retrieves_nothing_above_threshold() -> None:
    retriever = await build_corpus_retriever()

    assert await retriever.retrieve("What is the capital of France?", limit=3, min_score=0.2) == []


@pytest.mark.asyncio
async def test_draft_policy_is_not_in_verified_corpus() -> None:
    retriever = await build_corpus_retriever()

    results = await retriever.retrieve(
        "What is the daily meal allowance for travel?", limit=10, min_score=0.0
    )

    assert all(result.passage.document_slug != "travel-expenses" for result in results)


@pytest.mark.asyncio
async def test_empty_query_and_empty_index_return_nothing() -> None:
    empty = InMemoryKnowledgeRetriever(HashingEmbeddingProvider())

    assert await empty.retrieve("annual leave", limit=3, min_score=0.0) == []

    retriever = await build_corpus_retriever()

    assert await retriever.retrieve("   ", limit=3, min_score=0.0) == []
    assert await retriever.retrieve("annual leave", limit=0, min_score=0.0) == []
