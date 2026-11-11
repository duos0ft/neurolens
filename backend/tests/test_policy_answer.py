import json

import pytest

from app.ai.capabilities.text_generation import TextGenerationError
from app.services.policy_answer import (
    ABSTENTION_MESSAGE,
    AbstentionReason,
    PolicyAnswerService,
    PolicyAnswerStatus,
    PolicyCitation,
    normalize_for_matching,
    quote_is_supported,
)
from tests.helpers.knowledge import (
    CARRY_OVER_TEXT,
    StaticRetriever,
    build_corpus_retriever,
    make_passage,
)
from tests.helpers.mock_ai_provider import MockAIProvider


def draft(
    *facts: tuple[str, str, str],
    answerable: bool = True,
    explanation: str | None = "You can keep a few unused days, but use them by March.",
    missing: list[str] | None = None,
) -> str:
    return json.dumps(
        {
            "answerable": answerable,
            "facts": [
                {"statement": statement, "source_id": source_id, "quote": quote}
                for statement, source_id, quote in facts
            ],
            "explanation": explanation,
            "missing_information": missing or [],
        }
    )


CARRY_OVER_FACT = (
    "You can carry over up to five unused days.",
    "S1",
    "Employees may carry over up to five days of unused annual leave",
)

EXPIRY_FACT = (
    "Carried-over days must be used by 31 March.",
    "S1",
    "Carried-over leave must be used by 31 March of the following leave year.",
)


@pytest.mark.asyncio
async def test_answers_with_verified_citations() -> None:
    passage = make_passage()
    retriever = StaticRetriever([passage])
    provider = MockAIProvider(draft(CARRY_OVER_FACT, EXPIRY_FACT), model="policy-model")

    answer = await PolicyAnswerService(retriever, provider).answer("Can I carry over leave?")

    assert answer.status == PolicyAnswerStatus.ANSWERED
    assert answer.model == "policy-model"
    assert [fact.citation_number for fact in answer.facts] == [1, 1]
    assert len(answer.citations) == 1

    citation = answer.citations[0]

    assert citation.chunk_id == passage.chunk_id
    assert citation.document_title == "Annual Leave Policy"
    assert citation.section == "Carrying over leave"
    assert len(citation.quotes) == 2

    assert "**What the policy says**" in answer.content
    assert "- You can carry over up to five unused days. [1]" in answer.content
    assert "**What this means for you**" in answer.content
    assert (
        "[1] Annual Leave Policy, version 2.1 (effective 1 January 2026) — Carrying over leave"
        in answer.content
    )


@pytest.mark.asyncio
async def test_sends_question_and_labelled_sources_to_provider() -> None:
    retriever = StaticRetriever([make_passage()])
    provider = MockAIProvider(draft(CARRY_OVER_FACT))

    await PolicyAnswerService(retriever, provider, preference_instructions="Be brief.").answer(
        "Can I carry over leave?"
    )

    request = provider.requests[0]
    content = request.messages[0].content

    assert "Can I carry over leave?" in content
    assert "[S1] Annual Leave Policy (version 2.1, effective 2026-01-01)" in content
    assert CARRY_OVER_TEXT in content
    assert "Use only the provided excerpts" in request.system_instructions
    assert "Be brief." in request.system_instructions
    assert "never permit adding" in request.system_instructions


@pytest.mark.asyncio
async def test_abstains_without_calling_model_when_nothing_is_retrieved() -> None:
    provider = MockAIProvider(draft(CARRY_OVER_FACT))

    answer = await PolicyAnswerService(StaticRetriever([]), provider).answer("Pension?")

    assert answer.status == PolicyAnswerStatus.ABSTAINED
    assert answer.abstention_reason == AbstentionReason.NO_VERIFIED_SOURCES
    assert answer.content == ABSTENTION_MESSAGE
    assert answer.citations == ()
    assert provider.requests == []


@pytest.mark.asyncio
async def test_abstains_when_model_reports_unanswerable() -> None:
    provider = MockAIProvider(draft(answerable=False, explanation=None))

    answer = await PolicyAnswerService(StaticRetriever([make_passage()]), provider).answer(
        "How much parental leave pay do I get?"
    )

    assert answer.status == PolicyAnswerStatus.ABSTAINED
    assert answer.abstention_reason == AbstentionReason.INSUFFICIENT_EVIDENCE
    assert answer.citations == ()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fact",
    [
        # The quote is not in the excerpt (hallucinated number).
        ("You can carry over ten days.", "S1", "Employees may carry over up to ten days"),
        # The quote cites an excerpt that was never provided.
        CARRY_OVER_FACT[:1] + ("S9",) + CARRY_OVER_FACT[2:],
        # The quote is too short to be meaningful evidence.
        ("Leave is lost.", "S1", "is lost"),
    ],
)
async def test_abstains_when_no_fact_can_be_verified(fact: tuple[str, str, str]) -> None:
    provider = MockAIProvider(draft(fact))

    answer = await PolicyAnswerService(StaticRetriever([make_passage()]), provider).answer(
        "Can I carry over leave?"
    )

    assert answer.status == PolicyAnswerStatus.ABSTAINED
    assert answer.abstention_reason == AbstentionReason.INSUFFICIENT_EVIDENCE


@pytest.mark.asyncio
async def test_drops_unverified_facts_and_their_explanation() -> None:
    invented = ("Managers can approve ten days.", "S1", "Managers may approve up to ten days")
    provider = MockAIProvider(
        draft(CARRY_OVER_FACT, invented, explanation="Your manager can approve ten days.")
    )

    answer = await PolicyAnswerService(StaticRetriever([make_passage()]), provider).answer(
        "Can I carry over leave?"
    )

    assert answer.status == PolicyAnswerStatus.ANSWERED
    assert [fact.statement for fact in answer.facts] == [CARRY_OVER_FACT[0]]
    assert answer.explanation is None
    assert "ten days" not in answer.content


@pytest.mark.asyncio
async def test_numbers_citations_by_first_use_across_documents() -> None:
    leave = make_passage()
    remote = make_passage(
        "Employees in hybrid roles may work remotely for up to three days per week.",
        slug="remote-work",
        title="Remote Work Policy",
        section="Hybrid working pattern",
        source_version="1.3",
        effective_date=None,
    )
    provider = MockAIProvider(
        draft(
            (
                "Hybrid staff can work remotely three days a week.",
                "S2",
                "up to three days per week",
            ),
            CARRY_OVER_FACT,
        )
    )

    answer = await PolicyAnswerService(StaticRetriever([leave, remote]), provider).answer("Q?")

    assert [citation.document_slug for citation in answer.citations] == [
        "remote-work",
        "annual-leave",
    ]
    assert [fact.citation_number for fact in answer.facts] == [1, 2]
    assert "[1] Remote Work Policy, version 1.3 — Hybrid working pattern" in answer.content


@pytest.mark.asyncio
async def test_lists_missing_information_separately() -> None:
    provider = MockAIProvider(
        draft(CARRY_OVER_FACT, missing=["Whether carried-over days can be paid out."])
    )

    answer = await PolicyAnswerService(StaticRetriever([make_passage()]), provider).answer("Q?")

    assert "**Not covered by the policy**" in answer.content
    assert "- Whether carried-over days can be paid out." in answer.content


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content",
    [
        "not json",
        json.dumps({"answerable": True, "facts": [], "unexpected": 1}),
        json.dumps({"facts": []}),
    ],
)
async def test_invalid_model_output_raises_generation_error(content: str) -> None:
    provider = MockAIProvider(content)

    with pytest.raises(TextGenerationError):
        await PolicyAnswerService(StaticRetriever([make_passage()]), provider).answer("Q?")


@pytest.mark.asyncio
async def test_rejects_empty_question() -> None:
    with pytest.raises(ValueError):
        await PolicyAnswerService(StaticRetriever(), MockAIProvider("{}")).answer("   ")


def test_quote_matching_tolerates_formatting_only() -> None:
    passage = "- Employees **must** report a breach within 24 hours.\n- Reports go to “security”."

    assert quote_is_supported("Employees must report a breach within 24 hours", passage)
    assert quote_is_supported('Reports go to "security".', passage)
    assert quote_is_supported("EMPLOYEES MUST REPORT A BREACH", passage)
    assert not quote_is_supported("Employees must report a breach within 48 hours", passage)
    assert normalize_for_matching("  Hello,\n  world. ") == "hello, world"


def test_citation_round_trip_and_validation() -> None:
    passage = make_passage()
    citation = PolicyCitation(
        number=1,
        chunk_id=passage.chunk_id,
        document_id=passage.document_id,
        document_slug=passage.document_slug,
        document_title=passage.document_title,
        document_revision=3,
        source_version="2.1",
        effective_date=passage.effective_date,
        section=passage.section,
        quotes=("quote",),
    )

    assert PolicyCitation.from_dict(citation.to_dict()) == citation

    for broken in (
        {**citation.to_dict(), "number": 0},
        {**citation.to_dict(), "document_revision": "3"},
        {**citation.to_dict(), "chunk_id": "not-a-uuid"},
        {**citation.to_dict(), "document_title": ""},
        {**citation.to_dict(), "quotes": [1]},
    ):
        with pytest.raises(ValueError):
            PolicyCitation.from_dict(broken)


@pytest.mark.asyncio
async def test_end_to_end_with_corpus_retriever() -> None:
    """Real fictional documents + offline retrieval + scripted model draft."""

    retriever = await build_corpus_retriever()
    question = "How many days of annual leave do full-time employees get?"
    retrieved = await retriever.retrieve(question, limit=4, min_score=0.1)
    source_id = next(
        f"S{index}"
        for index, result in enumerate(retrieved, start=1)
        if result.passage.section == "Entitlement"
    )
    provider = MockAIProvider(
        draft(
            (
                "Full-time employees get 25 days of paid annual leave per year.",
                source_id,
                "Full-time employees receive 25 days of paid annual leave per leave year",
            )
        )
    )

    answer = await PolicyAnswerService(retriever, provider, min_score=0.1).answer(question)

    assert answer.status == PolicyAnswerStatus.ANSWERED
    assert answer.citations[0].document_slug == "annual-leave"
    assert answer.citations[0].section == "Entitlement"
