import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.capabilities.text_generation import (
    TextGenerationResponse,
    TextGenerationError,
    TextGenerationRequest,
)
from app.models.conversation import Conversation
from app.services.conversation import ConversationService


@pytest.mark.asyncio
async def test_employee_can_create_conversation(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    async with test_session_factory() as db:
        service = ConversationService(db)

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
        service = ConversationService(db)

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
        service = ConversationService(db)

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
        service = ConversationService(db)

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


from app.services.assistant import AssistantService


class MockTextGenerationProvider:
    def __init__(self) -> None:
        self.requests: list[TextGenerationRequest] = []

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        self.requests.append(request)

        return TextGenerationResponse(
            content="Here are three steps to complete your assignment.",
            model="mock-model",
        )


@pytest.mark.asyncio
async def test_conversation_persists_message_exchange(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider)

    async with test_session_factory() as db:
        service = ConversationService(db)
        conversation = await service.create(employee_id)

        result = await service.send_message(
            employee_id=employee_id,
            conversation_id=conversation.id,
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
            conversation_id=conversation.id,
        )

        assert messages is not None
        assert len(messages) == 2
        assert [message.role for message in messages] == [
            "user",
            "assistant",
        ]


@pytest.mark.asyncio
async def test_conversation_includes_previous_messages(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    provider = MockTextGenerationProvider()
    assistant = AssistantService(provider)

    async with test_session_factory() as db:
        service = ConversationService(db)
        conversation = await service.create(employee_id)

        await service.send_message(
            employee_id,
            conversation.id,
            "Explain my assignment.",
            assistant,
        )

        await service.send_message(
            employee_id,
            conversation.id,
            "What should I do first?",
            assistant,
        )

    assert len(provider.requests) == 2

    second_request = provider.requests[1]

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
        service = ConversationService(db)
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
