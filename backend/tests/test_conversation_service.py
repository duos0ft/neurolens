import asyncio
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.capabilities.text_generation import (
    TextGenerationError,
    TextGenerationRequest,
    TextGenerationResponse,
)
from app.ai.capabilities.types import AICapability
from app.ai.registry import AIProviderRegistry
from app.models.conversation import Conversation
from app.services.assistant import AssistantService
from app.services.assistant.assistant_orchestrator import AssistantOrchestrator
from app.services.assistant.assistant_response_composer import AssistantResponseComposer
from app.services.assistant.orchestrated_assistant import OrchestratedAssistantService
from app.services.conversation import ConversationService


class MockTextGenerationProvider:
    def __init__(self) -> None:
        self.assistant_requests: list[TextGenerationRequest] = []
        self.title_requests: list[TextGenerationRequest] = []
        self.fail_title = False
        self.timeout_title = False

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        is_title_request = (
            request.system_instructions is not None
            and "Generate a short, descriptive title" in request.system_instructions
        )

        if is_title_request:
            self.title_requests.append(request)

            if self.fail_title:
                raise TextGenerationError("Title provider unavailable")

            if self.timeout_title:
                raise TimeoutError("Title generation timed out")

            return TextGenerationResponse(
                content="Understanding Workplace Assignments",
                model="mock-model",
            )

        self.assistant_requests.append(request)

        return TextGenerationResponse(
            content="Here are three steps to complete your assignment.",
            model="mock-model",
        )


@pytest.mark.asyncio
async def test_employee_can_create_conversation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
        )

        conversation = await service.create(
            employee_id=employee_id,
            title="Workplace assistance",
        )

        assert conversation.id is not None
        assert conversation.employee_id == employee_id
        assert conversation.title == "Workplace assistance"

        stored = await db.get(Conversation, conversation.id)

        assert stored is not None
        assert stored.title == "Workplace assistance"


@pytest.mark.asyncio
async def test_employee_can_list_own_conversations(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
        )

        first = await service.create(employee_id, "First conversation")
        second = await service.create(employee_id, "Second conversation")

        conversations = await service.list(employee_id)

        ids = {conversation.id for conversation in conversations}

        assert first.id in ids
        assert second.id in ids


@pytest.mark.asyncio
async def test_employee_cannot_access_another_employees_conversation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    owner_id = test_invitation.employee_id
    another_employee_id = uuid.uuid4()

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
        )

        conversation = await service.create(
            employee_id=owner_id,
            title="Private conversation",
        )

        result = await service.get(
            employee_id=another_employee_id,
            conversation_id=conversation.id,
        )

        assert result is None

        messages = await service.get_messages(
            employee_id=another_employee_id,
            conversation_id=conversation.id,
        )

        assert messages is None

        deleted = await service.delete(
            employee_id=another_employee_id,
            conversation_id=conversation.id,
        )

        assert deleted is False

        stored = await db.get(Conversation, conversation.id)

        assert stored is not None


@pytest.mark.asyncio
async def test_employee_can_delete_own_conversation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
        )

        conversation = await service.create(
            employee_id=employee_id,
            title="Temporary conversation",
        )

        conversation_id = conversation.id

        deleted = await service.delete(
            employee_id=employee_id,
            conversation_id=conversation_id,
        )

        assert deleted is True

        stored = await db.get(Conversation, conversation_id)

        assert stored is None


@pytest.mark.asyncio
async def test_conversation_persists_message_exchange(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider)

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
            title_provider=provider,
        )

        conversation = await service.create(employee_id)
        conversation_id = conversation.id

        result = await service.send_message(
            employee_id=employee_id,
            conversation_id=conversation_id,
            content="Help me understand this assignment.",
            assistant=assistant,
        )

        assert result is not None

        user_message, assistant_message = result

        assert user_message.role == "user"
        assert user_message.content == "Help me understand this assignment."

        assert assistant_message.role == "assistant"
        assert assistant_message.content == ("Here are three steps to complete your assignment.")
        assert assistant_message.model == "mock-model"

        messages = await service.get_messages(
            employee_id=employee_id,
            conversation_id=conversation_id,
        )

        assert messages is not None
        assert len(messages) == 2
        assert [message.role for message in messages] == [
            "user",
            "assistant",
        ]

        assert len(provider.assistant_requests) == 1
        assert len(provider.title_requests) == 1


@pytest.mark.asyncio
async def test_conversation_includes_previous_messages(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider)

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
            title_provider=provider,
        )

        conversation = await service.create(employee_id)
        conversation_id = conversation.id

        await service.send_message(
            employee_id,
            conversation_id,
            "Explain my assignment.",
            assistant,
        )

        await service.send_message(
            employee_id,
            conversation_id,
            "What should I do first?",
            assistant,
        )

    assert len(provider.assistant_requests) == 2
    assert len(provider.title_requests) == 1

    second_request = provider.assistant_requests[1]

    assert [message.role for message in second_request.messages] == [
        "user",
        "assistant",
        "user",
    ]

    assert second_request.messages[-1].content == "What should I do first?"


@pytest.mark.asyncio
async def test_provider_failure_does_not_persist_messages(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider)

    async def failing_generate(
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        raise TextGenerationError("Provider unavailable")

    monkeypatch.setattr(provider, "generate", failing_generate)

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
            title_provider=provider,
        )

        conversation = await service.create(employee_id)
        conversation_id = conversation.id

        with pytest.raises(TextGenerationError):
            await service.send_message(
                employee_id,
                conversation_id,
                "Help me with this task.",
                assistant,
            )

        messages = await service.get_messages(
            employee_id=employee_id,
            conversation_id=conversation_id,
        )

        assert messages == []


@pytest.mark.asyncio
async def test_employee_can_rename_conversation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
        )

        conversation = await service.create(employee_id)

        renamed = await service.rename(
            employee_id=employee_id,
            conversation_id=conversation.id,
            title="  Preparing   for a meeting  ",
        )

        assert renamed is not None
        assert renamed.title == "Preparing for a meeting"

        stored = await service.get(employee_id, conversation.id)

        assert stored is not None
        assert stored.title == "Preparing for a meeting"


@pytest.mark.asyncio
async def test_employee_cannot_rename_another_conversation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    another_employee_id = uuid.uuid4()

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
        )

        conversation = await service.create(employee_id)

        renamed = await service.rename(
            employee_id=another_employee_id,
            conversation_id=conversation.id,
            title="Unauthorized rename",
        )

        assert renamed is None

        stored = await service.get(employee_id, conversation.id)

        assert stored is not None
        assert stored.title is None


@pytest.mark.asyncio
async def test_first_message_generates_conversation_title(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider)

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
            title_provider=provider,
        )

        conversation = await service.create(employee_id)
        conversation_id = conversation.id

        assert conversation.title is None

        result = await service.send_message(
            employee_id=employee_id,
            conversation_id=conversation_id,
            content="Help me understand this assignment.",
            assistant=assistant,
        )

        assert result is not None

        stored = await service.get(employee_id, conversation_id)

        assert stored is not None
        await db.refresh(stored)

        assert stored.title == "Understanding Workplace Assignments"
        assert len(provider.assistant_requests) == 1
        assert len(provider.title_requests) == 1


@pytest.mark.asyncio
async def test_follow_up_message_does_not_regenerate_title(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider)

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
            title_provider=provider,
        )

        conversation = await service.create(employee_id)
        conversation_id = conversation.id

        await service.send_message(
            employee_id,
            conversation_id,
            "Help me understand my assignment.",
            assistant,
        )

        await service.send_message(
            employee_id,
            conversation_id,
            "What should I do next?",
            assistant,
        )

        stored = await service.get(employee_id, conversation_id)

        assert stored is not None
        await db.refresh(stored)

        assert stored.title == "Understanding Workplace Assignments"

    assert len(provider.assistant_requests) == 2
    assert len(provider.title_requests) == 1


@pytest.mark.asyncio
async def test_manually_named_conversation_does_not_generate_title(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider)

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
            title_provider=provider,
        )

        conversation = await service.create(
            employee_id=employee_id,
            title="My own conversation title",
        )

        conversation_id = conversation.id

        result = await service.send_message(
            employee_id,
            conversation_id,
            "Help me prepare for a meeting.",
            assistant,
        )

        assert result is not None

        stored = await service.get(employee_id, conversation_id)

        assert stored is not None
        await db.refresh(stored)

        assert stored.title == "My own conversation title"

    assert len(provider.assistant_requests) == 1
    assert len(provider.title_requests) == 0


@pytest.mark.asyncio
async def test_manual_rename_is_preserved_after_follow_up(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider)

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
            title_provider=provider,
        )

        conversation = await service.create(employee_id)
        conversation_id = conversation.id

        await service.send_message(
            employee_id,
            conversation_id,
            "Help me understand my assignment.",
            assistant,
        )

        renamed = await service.rename(
            employee_id=employee_id,
            conversation_id=conversation_id,
            title="My study plan",
        )

        assert renamed is not None
        assert renamed.title == "My study plan"

        await service.send_message(
            employee_id,
            conversation_id,
            "What should I do tomorrow?",
            assistant,
        )

        stored = await service.get(employee_id, conversation_id)

        assert stored is not None
        await db.refresh(stored)

        assert stored.title == "My study plan"

    assert len(provider.title_requests) == 1


@pytest.mark.asyncio
async def test_title_generation_failure_preserves_messages(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    provider.fail_title = True

    assistant = AssistantService(provider)

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
            title_provider=provider,
        )

        conversation = await service.create(employee_id)
        conversation_id = conversation.id

        result = await service.send_message(
            employee_id,
            conversation_id,
            "Help me organize my tasks.",
            assistant,
        )

        assert result is not None

        messages = await service.get_messages(
            employee_id,
            conversation_id,
        )

        assert messages is not None
        assert len(messages) == 2

        stored = await service.get(employee_id, conversation_id)

        assert stored is not None
        await db.refresh(stored)

        assert stored.title is None

    assert len(provider.assistant_requests) == 1
    assert len(provider.title_requests) == 1


@pytest.mark.asyncio
async def test_title_generation_timeout_preserves_messages(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    provider.timeout_title = True

    assistant = AssistantService(provider)

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
            title_provider=provider,
        )

        conversation = await service.create(employee_id)
        conversation_id = conversation.id

        result = await service.send_message(
            employee_id,
            conversation_id,
            "Help me prepare for a meeting.",
            assistant,
        )

        assert result is not None

        messages = await service.get_messages(
            employee_id,
            conversation_id,
        )

        assert messages is not None
        assert len(messages) == 2

        stored = await service.get(employee_id, conversation_id)

        assert stored is not None
        await db.refresh(stored)

        assert stored.title is None

    assert len(provider.assistant_requests) == 1
    assert len(provider.title_requests) == 1


@pytest.mark.asyncio
async def test_title_failure_does_not_expire_main_session_objects(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    provider.fail_title = True

    assistant = AssistantService(provider)

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
            title_provider=provider,
        )

        conversation = await service.create(employee_id)
        conversation_id = conversation.id

        result = await service.send_message(
            employee_id=employee_id,
            conversation_id=conversation_id,
            content="Help me organize my tasks.",
            assistant=assistant,
        )

        assert result is not None

        # A failed title-generation call must not roll back
        # or expire ORM objects in the main session.
        assert conversation.id == conversation_id

        user_message, assistant_message = result

        assert user_message.role == "user"
        assert user_message.content == "Help me organize my tasks."
        assert assistant_message.role == "assistant"
        assert assistant_message.model == "mock-model"

        messages = await service.get_messages(
            employee_id=employee_id,
            conversation_id=conversation_id,
        )

        assert messages is not None
        assert len(messages) == 2

        stored = await service.get(employee_id, conversation_id)

        assert stored is not None
        await db.refresh(stored)

        assert stored.title is None

    assert len(provider.assistant_requests) == 1
    assert len(provider.title_requests) == 1


@pytest.mark.asyncio
async def test_manual_rename_wins_during_title_generation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider)

    title_started = asyncio.Event()
    allow_title_to_finish = asyncio.Event()

    original_generate = provider.generate

    async def delayed_generate(
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        if (
            request.system_instructions is not None
            and "Generate a short, descriptive title" in request.system_instructions
        ):
            title_started.set()
            await allow_title_to_finish.wait()

        return await original_generate(request)

    monkeypatch.setattr(provider, "generate", delayed_generate)

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
            title_provider=provider,
        )

        conversation = await service.create(employee_id)
        conversation_id = conversation.id

        send_task = asyncio.create_task(
            service.send_message(
                employee_id=employee_id,
                conversation_id=conversation_id,
                content="Help me prepare for a meeting.",
                assistant=assistant,
            )
        )

        try:
            await asyncio.wait_for(title_started.wait(), timeout=3)

            # Rename using a separate database session,
            # simulating another request from the frontend.
            async with test_session_factory() as rename_db:
                rename_service = ConversationService(
                    db=rename_db,
                    session_factory=test_session_factory,
                )

                renamed = await rename_service.rename(
                    employee_id=employee_id,
                    conversation_id=conversation_id,
                    title="My meeting preparation",
                )

                assert renamed is not None
                assert renamed.title == "My meeting preparation"

        finally:
            allow_title_to_finish.set()
            await send_task

        await db.refresh(conversation)

        assert conversation.title == "My meeting preparation"

    assert len(provider.assistant_requests) == 1
    assert len(provider.title_requests) == 1


@pytest.mark.asyncio
async def test_missing_title_provider_preserves_messages(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider)

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
            title_provider=None,
        )

        conversation = await service.create(employee_id)

        result = await service.send_message(
            employee_id=employee_id,
            conversation_id=conversation.id,
            content="Help me organize my tasks.",
            assistant=assistant,
        )

        assert result is not None

        messages = await service.get_messages(
            employee_id=employee_id,
            conversation_id=conversation.id,
        )

        assert messages is not None
        assert len(messages) == 2

        await db.refresh(conversation)

        assert conversation.title is None
        assert len(provider.assistant_requests) == 1
        assert len(provider.title_requests) == 0


@pytest.mark.asyncio
async def test_orchestrated_assistant_persists_capability_metadata(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    registry = AIProviderRegistry()

    classifier = MockTextGenerationProvider()
    explanation = MockTextGenerationProvider()

    async def classify(
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        return TextGenerationResponse(
            content=(
                '{"intents": ['
                '{"capability": "message_explanation", '
                '"instruction": "Explain the workplace message.", '
                '"source_text": null}'
                "]}"
            ),
            model="mock-classifier",
        )

    async def generate_explanation(
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        explanation.assistant_requests.append(request)

        return TextGenerationResponse(
            content=(
                '{"explanation": "EOD means end of day.", '
                '"ambiguities": [], '
                '"steps": [], '
                '"next_step": null}'
            ),
            model="mock-model",
        )

    classifier.generate = classify
    explanation.generate = generate_explanation

    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION,
        classifier,
    )

    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        explanation,
    )

    assistant = OrchestratedAssistantService(
        orchestrator=AssistantOrchestrator(
            registry=registry,
        ),
        composer=AssistantResponseComposer(),
    )

    async with test_session_factory() as db:
        service = ConversationService(
            db=db,
            session_factory=test_session_factory,
        )

        conversation = await service.create(employee_id)

        result = await service.send_message(
            employee_id=employee_id,
            conversation_id=conversation.id,
            content="Explain what EOD means.",
            assistant=assistant,
        )

        assert result is not None

        user_message, assistant_message = result

        assert user_message.role == "user"
        assert user_message.content == "Explain what EOD means."
        assert user_message.capability_metadata is None

        assert assistant_message.role == "assistant"
        assert assistant_message.content == "EOD means end of day."
        assert assistant_message.model == "mock-model"
        assert assistant_message.task_suggestions is None

        assert assistant_message.capability_metadata == {
            "version": 2,
            "capabilities": [
                "message_explanation",
            ],
            "sources": [],
        }

        stored_messages = await service.get_messages(
            employee_id=employee_id,
            conversation_id=conversation.id,
        )

        assert stored_messages is not None
        assert len(stored_messages) == 2

        assert stored_messages[0].content == "Explain what EOD means."
        assert stored_messages[1].content == "EOD means end of day."

        assert stored_messages[1].capability_metadata == {
            "version": 2,
            "capabilities": [
                "message_explanation",
            ],
            "sources": [],
        }

        assert stored_messages[1].task_suggestions is None

    assert len(explanation.assistant_requests) == 1

    request = explanation.assistant_requests[0]

    assert request.system_instructions is not None
    assert "Structured explanation output:" in request.system_instructions
    assert "Explain the workplace message." in request.messages[0].content
