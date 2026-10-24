import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.capabilities.text_generation import (
    TextGenerationError,
    TextGenerationRequest,
    TextGenerationResponse,
)
from app.api.assistant import get_assistant_service
from app.core.database import get_db
from app.core.settings import settings
from app.main import create_app
from app.models.employee import Employee
from app.models.employee_session import EmployeeSession
from app.services.assistant import AssistantService
from app.services.conversation import ConversationService
from app.services.oauth import generate_token, hash_token


class MockTextGenerationProvider:
    def __init__(self) -> None:
        self.requests: list[TextGenerationRequest] = []
        self.should_fail = False

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        self.requests.append(request)

        if self.should_fail:
            raise TextGenerationError("Internal provider connection details")

        return TextGenerationResponse(
            content="Start by reviewing the assignment requirements.",
            model="mock-model",
        )


@pytest.fixture
def mock_provider() -> MockTextGenerationProvider:
    return MockTextGenerationProvider()


@pytest.fixture
async def authenticated_client(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
    mock_provider: MockTextGenerationProvider,
) -> AsyncIterator[tuple[httpx.AsyncClient, uuid.UUID]]:
    employee_id = test_invitation.employee_id
    session_token = generate_token()
    now = datetime.now(timezone.utc)

    async with test_session_factory() as db:
        employee = await db.get(Employee, employee_id)

        assert employee is not None

        employee.status = "active"

        db.add(
            EmployeeSession(
                employee_id=employee_id,
                session_hash=hash_token(session_token),
                last_active_at=now,
                expires_at=now + timedelta(days=7),
            )
        )

        await db.commit()

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_assistant_service] = lambda: AssistantService(
        provider=mock_provider
    )

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url=settings.frontend_url,
            headers={
                "Origin": settings.frontend_url,
            },
        ) as client:
            client.cookies.set(
                settings.session_cookie_name,
                session_token,
                path="/",
            )

            csrf_protect = CsrfProtect()
            csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

            client.cookies.set(
                csrf_protect._cookie_key,
                signed_token,
                path="/",
            )

            client.headers["X-CSRF-Token"] = csrf_token

            yield client, employee_id

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_employee_can_create_conversation(
    authenticated_client,
) -> None:
    client, _ = authenticated_client

    response = await client.post(
        "/api/conversations",
        json={
            "title": "Workplace assistance",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert uuid.UUID(data["id"])
    assert data["title"] == "Workplace assistance"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_employee_can_list_conversations(
    authenticated_client,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={
            "title": "My conversation",
        },
    )

    assert created.status_code == 201

    response = await client.get("/api/conversations")

    assert response.status_code == 200

    assert any(conversation["id"] == created.json()["id"] for conversation in response.json())


@pytest.mark.asyncio
async def test_employee_can_get_conversation(
    authenticated_client,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={
            "title": "Project planning",
        },
    )

    assert created.status_code == 201

    response = await client.get(f"/api/conversations/{created.json()['id']}")

    assert response.status_code == 200
    assert response.json()["title"] == "Project planning"
    assert response.json()["messages"] == []


@pytest.mark.asyncio
async def test_employee_cannot_access_another_conversation(
    authenticated_client,
    test_session_factory: async_sessionmaker[AsyncSession],
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    mock_provider: MockTextGenerationProvider,
) -> None:
    client, _ = authenticated_client

    other_employee_id = uuid.uuid4()

    async with test_admin_session_factory() as db:
        other_employee = Employee(
            user_id=other_employee_id,
            email=f"other-{other_employee_id.hex}@example.com",
            role="employee",
            status="active",
            provisioning_status="completed",
        )

        db.add(other_employee)
        await db.commit()

    try:
        async with test_session_factory() as db:
            service = ConversationService(db)

            conversation = await service.create(
                employee_id=other_employee_id,
                title="Private conversation",
            )

            conversation_id = conversation.id

        get_response = await client.get(f"/api/conversations/{conversation_id}")

        delete_response = await client.delete(f"/api/conversations/{conversation_id}")

        message_response = await client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={
                "content": "Show me this private conversation.",
            },
        )

        assert get_response.status_code == 404
        assert delete_response.status_code == 404
        assert message_response.status_code == 404

        assert mock_provider.requests == []

        async with test_session_factory() as db:
            service = ConversationService(db)

            stored = await service.get(
                employee_id=other_employee_id,
                conversation_id=conversation_id,
            )

            assert stored is not None

            messages = await service.get_messages(
                employee_id=other_employee_id,
                conversation_id=conversation_id,
            )

            assert messages == []

    finally:
        async with test_admin_session_factory() as db:
            await db.execute(
                delete(Employee).where(
                    Employee.user_id == other_employee_id,
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_employee_can_delete_own_conversation(
    authenticated_client,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={
            "title": "Temporary conversation",
        },
    )

    assert created.status_code == 201

    conversation_id = created.json()["id"]

    response = await client.delete(f"/api/conversations/{conversation_id}")

    assert response.status_code == 204

    get_response = await client.get(f"/api/conversations/{conversation_id}")

    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_conversation_requires_csrf(
    authenticated_client,
) -> None:
    client, _ = authenticated_client

    response = await client.post(
        "/api/conversations",
        json={
            "title": "Unauthorized conversation",
        },
        headers={
            "X-CSRF-Token": "",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_employee_cannot_list_conversations(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url=settings.frontend_url,
        ) as client:
            response = await client.get("/api/conversations")

        assert response.status_code == 401

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_employee_can_send_conversation_message(
    authenticated_client,
    mock_provider: MockTextGenerationProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={
            "title": "Workplace assistance",
        },
    )

    assert created.status_code == 201

    conversation_id = created.json()["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "What should I do first?",
        },
    )

    assert response.status_code == 201

    messages = response.json()

    assert len(messages) == 2

    assert [message["role"] for message in messages] == [
        "user",
        "assistant",
    ]

    assert messages[0]["content"] == "What should I do first?"
    assert messages[1]["content"] == ("Start by reviewing the assignment requirements.")

    assert messages[1]["model"] == "mock-model"

    assert len(mock_provider.requests) == 1

    request = mock_provider.requests[0]

    assert len(request.messages) == 1
    assert request.messages[0].role == "user"
    assert request.messages[0].content == "What should I do first?"

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200

    stored_messages = detail.json()["messages"]

    assert len(stored_messages) == 2
    assert [message["role"] for message in stored_messages] == [
        "user",
        "assistant",
    ]


@pytest.mark.asyncio
async def test_conversation_messages_include_previous_history(
    authenticated_client,
    mock_provider: MockTextGenerationProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={
            "title": "Assignment planning",
        },
    )

    assert created.status_code == 201

    conversation_id = created.json()["id"]

    first_response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Explain my assignment.",
        },
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "What should I do next?",
        },
    )

    assert second_response.status_code == 201
    assert len(mock_provider.requests) == 2

    second_request = mock_provider.requests[1]

    assert [message.role for message in second_request.messages] == [
        "user",
        "assistant",
        "user",
    ]

    assert second_request.messages[0].content == ("Explain my assignment.")

    assert second_request.messages[1].content == ("Start by reviewing the assignment requirements.")

    assert second_request.messages[2].content == ("What should I do next?")

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200

    messages = detail.json()["messages"]

    assert len(messages) == 4

    assert [message["role"] for message in messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]


@pytest.mark.asyncio
async def test_provider_failure_does_not_save_messages(
    authenticated_client,
    mock_provider: MockTextGenerationProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={
            "title": "Provider failure test",
        },
    )

    assert created.status_code == 201

    conversation_id = created.json()["id"]

    mock_provider.should_fail = True

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Help me understand this task.",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": "The AI assistant is temporarily unavailable",
    }

    assert "Internal provider connection details" not in response.text

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200
    assert detail.json()["messages"] == []


@pytest.mark.asyncio
async def test_send_conversation_message_requires_csrf(
    authenticated_client,
    mock_provider: MockTextGenerationProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={
            "title": "CSRF test",
        },
    )

    assert created.status_code == 201

    conversation_id = created.json()["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "This request should be rejected.",
        },
        headers={
            "X-CSRF-Token": "",
        },
    )

    assert response.status_code == 403
    assert mock_provider.requests == []
