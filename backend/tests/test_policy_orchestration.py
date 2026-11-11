import json
import uuid
from datetime import datetime, timezone

import pytest

from app.ai.capabilities.embeddings import EmbeddingError
from app.ai.capabilities.text_generation import TextGenerationError
from app.ai.capabilities.types import AICapability
from app.ai.providers.local_embeddings import HashingEmbeddingProvider
from app.ai.registry import AIProviderRegistry
from app.ai.resolver import resolve_ai_provider_registry
from app.api.assistant_dependencies import build_policy_answerer
from app.core.settings import settings
from app.models.conversation_message import ConversationMessage
from app.schemas.conversation import ConversationMessageResponse
from app.services.assistant_config import AssistantConfig
from app.services.assistant_orchestrator import (
    OMITTED_SOURCE_PLACEHOLDER,
    AssistantOrchestrator,
    build_policy_query,
)
from app.services.assistant_response_composer import AssistantResponseComposer
from app.services.capability_intent import CapabilityIntent
from app.services.conversation_capability_metadata import ConversationCapabilityMetadata
from app.services.conversation_snapshot_builder import ConversationSnapshotBuilder
from app.services.knowledge_retrieval import DatabaseKnowledgeRetriever
from app.services.orchestrated_assistant import OrchestratedAssistantService
from app.services.policy_answer import PolicyAnswerService, PolicyAnswerStatus, PolicyCitation
from tests.helpers.ai_responses import explanation_response
from tests.helpers.knowledge import StaticRetriever, make_passage
from tests.helpers.mock_ai_provider import MockAIProvider

POLICY_DRAFT = json.dumps(
    {
        "answerable": True,
        "facts": [
            {
                "statement": "You can carry over up to five unused days.",
                "source_id": "S1",
                "quote": "Employees may carry over up to five days of unused annual leave",
            }
        ],
        "explanation": None,
        "missing_information": [],
    }
)

SOURCE = "Please send me your availability."


def classification(*intents: tuple[str, str | None]) -> str:
    return json.dumps(
        {
            "intents": [
                {
                    "capability": capability,
                    "instruction": f"Handle {capability}.",
                    "source_text": source_text,
                }
                for capability, source_text in intents
            ]
        }
    )


def build_assistant(
    classifier_output: str,
    *,
    enable_policy: bool = True,
    retriever: StaticRetriever | None = None,
    policy_provider: MockAIProvider | None = None,
) -> tuple[OrchestratedAssistantService, StaticRetriever, MockAIProvider, MockAIProvider]:
    registry = AIProviderRegistry()
    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION, MockAIProvider(classifier_output)
    )
    explanation = MockAIProvider(
        explanation_response("Your manager wants your availability.").content
    )
    registry.register_text_generation(AICapability.MESSAGE_EXPLANATION, explanation)

    retriever = retriever or StaticRetriever([make_passage()])
    policy_provider = policy_provider or MockAIProvider(POLICY_DRAFT, model="policy-model")

    orchestrator = AssistantOrchestrator(
        registry,
        config=AssistantConfig(enable_policy_assistance=enable_policy),
        policy_answerer=PolicyAnswerService(retriever, policy_provider),
    )

    return (
        OrchestratedAssistantService(orchestrator, AssistantResponseComposer()),
        retriever,
        policy_provider,
        explanation,
    )


@pytest.mark.asyncio
async def test_policy_question_is_answered_with_citations() -> None:
    assistant, retriever, policy_provider, _ = build_assistant(
        classification(("policy_question", None))
    )

    result = await assistant.execute("Can I carry over my annual leave?")

    assert result.capabilities == (AICapability.POLICY_QUESTION,)
    assert result.policy_status == PolicyAnswerStatus.ANSWERED
    assert len(result.citations) == 1
    assert result.response.model == "policy-model"
    assert "[1] Annual Leave Policy" in result.response.content
    assert retriever.queries[0].startswith("Can I carry over my annual leave?")
    assert len(policy_provider.requests) == 1


@pytest.mark.asyncio
async def test_organization_flag_off_refers_without_retrieval() -> None:
    assistant, retriever, policy_provider, _ = build_assistant(
        classification(("policy_question", None)),
        enable_policy=False,
    )

    result = await assistant.execute("Can I carry over my annual leave?")

    assert "can't verify" in result.response.content
    assert result.policy_status is None
    assert result.citations == ()
    assert retriever.queries == []
    assert policy_provider.requests == []


@pytest.mark.asyncio
async def test_abstention_is_recorded_without_citations() -> None:
    assistant, _, policy_provider, _ = build_assistant(
        classification(("policy_question", None)),
        retriever=StaticRetriever([]),
    )

    result = await assistant.execute("What is the pension contribution?")

    assert result.policy_status == PolicyAnswerStatus.ABSTAINED
    assert result.citations == ()
    assert "won't guess" in result.response.content
    assert policy_provider.requests == []


@pytest.mark.asyncio
async def test_mixed_request_answers_policy_without_quoted_source_text() -> None:
    assistant, retriever, policy_provider, explanation = build_assistant(
        classification(("message_explanation", SOURCE), ("policy_question", None))
    )

    result = await assistant.execute(
        f'My manager wrote: "{SOURCE}" Explain it and tell me if I can carry over leave.'
    )

    assert result.capabilities == (
        AICapability.MESSAGE_EXPLANATION,
        AICapability.POLICY_QUESTION,
    )
    assert "### What this means" in result.response.content
    assert "### Company policy" in result.response.content
    assert result.policy_status == PolicyAnswerStatus.ANSWERED

    # Third-party quoted text never reaches policy retrieval or generation.
    assert SOURCE not in retriever.queries[0]
    assert OMITTED_SOURCE_PLACEHOLDER in retriever.queries[0]
    assert SOURCE not in policy_provider.requests[0].messages[0].content

    # Policy content never reaches the explanation specialist.
    assert "carry over" not in explanation.requests[0].messages[0].content

    # Mixed results can now be persisted (previously raised ValueError).
    metadata = ConversationCapabilityMetadata.from_execution_result(result)
    restored = ConversationCapabilityMetadata.from_dict(metadata.to_dict())

    assert restored == metadata
    assert len(restored.sources) == 1
    assert len(restored.citations) == 1


@pytest.mark.asyncio
async def test_mixed_request_without_isolated_source_still_refuses() -> None:
    assistant, retriever, _, explanation = build_assistant(
        classification(("message_explanation", None), ("policy_question", None))
    )

    result = await assistant.execute("Explain this HR message and tell me our leave policy.")

    assert "can't safely separate" in result.response.content
    assert retriever.queries == []
    assert explanation.requests == []


@pytest.mark.asyncio
async def test_embedding_failure_surfaces_as_generation_error() -> None:
    class FailingRetriever(StaticRetriever):
        async def retrieve(self, query, *, limit, min_score):
            raise EmbeddingError("down")

    assistant, _, _, _ = build_assistant(
        classification(("policy_question", None)),
        retriever=FailingRetriever(),
    )

    with pytest.raises(TextGenerationError):
        await assistant.execute("Can I carry over leave?")


def test_build_policy_query_removes_sources_and_adds_context() -> None:
    message = f'Manager: "{SOURCE}" Also, what about part-time staff?'
    snapshot = ConversationSnapshotBuilder().build(
        message=message,
        intent=CapabilityIntent(
            capability=AICapability.MESSAGE_EXPLANATION,
            instruction="Explain.",
            source_text=SOURCE,
        ),
    )

    assert snapshot is not None

    query = build_policy_query(
        message,
        CapabilityIntent(
            capability=AICapability.POLICY_QUESTION,
            instruction="Annual leave entitlement for part-time staff.",
        ),
        [snapshot],
    )

    assert SOURCE not in query
    assert "what about part-time staff?" in query
    assert query.endswith("Context: Annual leave entitlement for part-time staff.")


def test_metadata_rejects_inconsistent_policy_data() -> None:
    passage = make_passage()
    citation = PolicyCitation(
        number=1,
        chunk_id=passage.chunk_id,
        document_id=passage.document_id,
        document_slug="annual-leave",
        document_title="Annual Leave Policy",
        document_revision=1,
        source_version="2.1",
        effective_date=None,
        section=None,
    )

    with pytest.raises(ValueError, match="requires a policy capability"):
        ConversationCapabilityMetadata(
            capabilities=(AICapability.GENERAL_CONVERSATION,),
            policy_status=PolicyAnswerStatus.ANSWERED,
            citations=(citation,),
        )

    with pytest.raises(ValueError, match="Only answered"):
        ConversationCapabilityMetadata(
            capabilities=(AICapability.POLICY_QUESTION,),
            policy_status=PolicyAnswerStatus.ABSTAINED,
            citations=(citation,),
        )

    with pytest.raises(ValueError, match="must carry citations"):
        ConversationCapabilityMetadata(
            capabilities=(AICapability.POLICY_QUESTION,),
            policy_status=PolicyAnswerStatus.ANSWERED,
        )

    with pytest.raises(ValueError, match="sequential"):
        ConversationCapabilityMetadata(
            capabilities=(AICapability.POLICY_QUESTION,),
            policy_status=PolicyAnswerStatus.ANSWERED,
            citations=(citation, citation),
        )


def test_version_two_metadata_still_parses() -> None:
    metadata = ConversationCapabilityMetadata.from_dict(
        {"version": 2, "capabilities": ["policy_question"], "sources": []}
    )

    assert metadata.policy_status is None
    assert metadata.citations == ()


@pytest.mark.asyncio
async def test_message_response_exposes_stored_citations() -> None:
    assistant, _, _, _ = build_assistant(classification(("policy_question", None)))
    result = await assistant.execute("Can I carry over my annual leave?")

    message = ConversationMessage(
        id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        sequence_number=2,
        role="assistant",
        content=result.response.content,
        model=result.response.model,
        created_at=datetime.now(timezone.utc),
        capability_metadata=ConversationCapabilityMetadata.from_execution_result(result).to_dict(),
    )

    response = ConversationMessageResponse.model_validate(message, from_attributes=True)

    assert len(response.citations) == 1
    assert response.citations[0].document_slug == "annual-leave"
    assert response.citations[0].quotes

    message.capability_metadata = {"version": 99}
    assert ConversationMessageResponse.model_validate(message).citations == []

    message.capability_metadata = None
    assert ConversationMessageResponse.model_validate(message).citations == []


def test_resolver_registers_embeddings_and_policy_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_text_generation_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-api-key")
    monkeypatch.setattr(settings, "ai_embedding_provider", "local")

    registry = resolve_ai_provider_registry()

    assert registry.get_embeddings().model_id.startswith("local:")
    assert registry.get_text_generation(AICapability.POLICY_GENERATION) is not None


def test_resolver_rejects_unknown_embedding_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "openai_api_key", "test-api-key")
    monkeypatch.setattr(settings, "ai_embedding_provider", "nope")

    with pytest.raises(ValueError, match="Unsupported embedding provider"):
        resolve_ai_provider_registry()


def test_policy_answerer_is_only_built_when_enabled_and_configured() -> None:
    registry = AIProviderRegistry()
    enabled = AssistantConfig(enable_policy_assistance=True)

    assert build_policy_answerer(None, registry, AssistantConfig()) is None
    assert build_policy_answerer(None, registry, enabled) is None

    registry.register_embeddings(HashingEmbeddingProvider())
    assert build_policy_answerer(None, registry, enabled) is None

    registry.register_text_generation(AICapability.POLICY_GENERATION, MockAIProvider("{}"))
    answerer = build_policy_answerer(None, registry, enabled)

    assert isinstance(answerer, PolicyAnswerService)
    assert isinstance(answerer.retriever, DatabaseKnowledgeRetriever)
    assert build_policy_answerer(None, registry, AssistantConfig()) is None
