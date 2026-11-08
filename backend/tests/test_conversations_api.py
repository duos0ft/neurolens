import json
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
from app.ai.capabilities.types import AICapability
from app.ai.registry import AIProviderRegistry
from app.api.assistant_dependencies import get_ai_provider_registry
from app.core.database import get_db, get_session_factory
from app.core.settings import settings
from app.main import create_app
from app.models.employee import Employee
from app.models.employee_session import EmployeeSession
from app.services.assistant_orchestrator import (
    AssistantOrchestrator,
    CapabilityDisabledError,
)
from app.services.conversation import ConversationService
from app.services.oauth import generate_token, hash_token


class MockTextGenerationProvider:
    def __init__(self) -> None:
        self.assistant_requests: list[TextGenerationRequest] = []
        self.title_requests: list[TextGenerationRequest] = []
        self.should_fail = False
        self.should_fail_title = False

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

            if self.should_fail_title:
                raise TextGenerationError("Title generation unavailable")

            return TextGenerationResponse(
                content="Understanding Workplace Assignments",
                model="mock-model",
            )

        self.assistant_requests.append(request)

        if self.should_fail:
            raise TextGenerationError("Internal provider connection details")

        return TextGenerationResponse(
            content="Start by reviewing the assignment requirements.",
            model="mock-model",
        )


class MockClassificationProvider:
    def __init__(self) -> None:
        self.requests: list[TextGenerationRequest] = []

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        self.requests.append(request)

        return TextGenerationResponse(
            content=(
                '{"intents": ['
                '{"capability": "message_explanation", '
                '"instruction": "Explain the employee request.", '
                '"source_text": null}'
                "]}"
            ),
            model="mock-classifier",
        )


class MockTaskExtractionProvider:
    def __init__(self) -> None:
        self.requests: list[TextGenerationRequest] = []
        self.should_fail = False
        self.invalid_json = False

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        self.requests.append(request)

        if self.should_fail:
            raise TextGenerationError("Internal extraction provider details")

        if self.invalid_json:
            return TextGenerationResponse(
                content="invalid JSON",
                model="mock-extraction",
            )

        return TextGenerationResponse(
            content=json.dumps(
                {
                    "tasks": [
                        {
                            "title": "Review client feedback",
                            "description": "Identify important issues.",
                            "priority": None,
                            "due_date": None,
                            "source_text": "Review last week's client feedback",
                            "subtasks": [],
                        },
                    ],
                }
            ),
            model="mock-extraction",
        )


@pytest.fixture
def mock_provider() -> MockTextGenerationProvider:
    return MockTextGenerationProvider()


@pytest.fixture
def mock_classifier() -> MockClassificationProvider:
    return MockClassificationProvider()


@pytest.fixture
def mock_task_extraction() -> MockTaskExtractionProvider:
    return MockTaskExtractionProvider()


@pytest.fixture
async def authenticated_client(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
    mock_provider: MockTextGenerationProvider,
    mock_classifier: MockClassificationProvider,
    mock_task_extraction: MockTaskExtractionProvider,
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

    registry = AIProviderRegistry()

    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION,
        mock_classifier,
    )

    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        mock_provider,
    )

    registry.register_text_generation(
        AICapability.TASK_ASSISTANCE,
        mock_provider,
    )

    registry.register_text_generation(
        AICapability.TASK_EXTRACTION,
        mock_task_extraction,
    )

    registry.register_text_generation(
        AICapability.GENERAL_CONVERSATION,
        mock_provider,
    )

    registry.register_text_generation(
        AICapability.CONVERSATION_TITLE,
        mock_provider,
    )

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_session_factory] = lambda: test_session_factory
    app.dependency_overrides[get_ai_provider_registry] = lambda: registry

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

    assert response.status_code == 201, response.text

    data = response.json()

    assert uuid.UUID(data["id"])
    assert data["title"] == "Workplace assistance"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_employee_can_create_untitled_conversation(
    authenticated_client,
) -> None:
    client, _ = authenticated_client

    response = await client.post(
        "/api/conversations",
        json={},
    )

    assert response.status_code == 201, response.text
    assert response.json()["title"] is None


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

    assert created.status_code == 201, created.text

    response = await client.get("/api/conversations")

    assert response.status_code == 200, response.text

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

    assert created.status_code == 201, created.text

    response = await client.get(f"/api/conversations/{created.json()['id']}")

    assert response.status_code == 200, response.text
    assert response.json()["title"] == "Project planning"
    assert response.json()["messages"] == []


@pytest.mark.asyncio
async def test_employee_cannot_access_another_conversation(
    authenticated_client,
    test_session_factory: async_sessionmaker[AsyncSession],
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    mock_provider: MockTextGenerationProvider,
    mock_classifier: MockClassificationProvider,
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
            service = ConversationService(
                db=db,
                session_factory=test_session_factory,
            )

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

        assert mock_provider.assistant_requests == []
        assert mock_provider.title_requests == []
        assert mock_classifier.requests == []

        async with test_session_factory() as db:
            service = ConversationService(
                db=db,
                session_factory=test_session_factory,
            )

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

    assert created.status_code == 201, created.text

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
    mock_classifier: MockClassificationProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={
            "title": "Workplace assistance",
        },
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "What should I do first?",
        },
    )

    assert response.status_code == 201, response.text

    messages = response.json()

    assert len(messages) == 2

    assert [message["role"] for message in messages] == [
        "user",
        "assistant",
    ]

    assert messages[0]["content"] == "What should I do first?"
    assert messages[1]["content"] == ("Start by reviewing the assignment requirements.")
    assert messages[1]["model"] == "mock-model"

    assert len(mock_classifier.requests) == 1
    assert len(mock_provider.assistant_requests) == 1
    assert len(mock_provider.title_requests) == 0

    request = mock_provider.assistant_requests[0]

    assert len(request.messages) == 1
    assert request.messages[0].role == "user"

    assert "What should I do first?" in request.messages[0].content
    assert "Explain the employee request." in request.messages[0].content

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200, detail.text

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
    mock_classifier: MockClassificationProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={
            "title": "Assignment planning",
        },
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    first_response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Explain my assignment.",
        },
    )

    assert first_response.status_code == 201, first_response.text

    second_response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "What should I do next?",
        },
    )

    assert second_response.status_code == 201, second_response.text

    assert len(mock_classifier.requests) == 2
    assert len(mock_provider.assistant_requests) == 2
    assert len(mock_provider.title_requests) == 0

    second_request = mock_provider.assistant_requests[1]

    assert len(second_request.messages) == 3

    assert second_request.messages[0].role == "user"
    assert second_request.messages[1].role == "assistant"
    assert second_request.messages[2].role == "user"

    assert "What should I do next?" in second_request.messages[2].content
    assert second_request.messages[0].content == "Explain my assignment."

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200, detail.text

    messages = detail.json()["messages"]

    assert len(messages) == 4

    assert [message["role"] for message in messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]

    assert [message["content"] for message in messages if message["role"] == "user"] == [
        "Explain my assignment.",
        "What should I do next?",
    ]

    assert all(
        message["content"] == ("Start by reviewing the assignment requirements.")
        for message in messages
        if message["role"] == "assistant"
    )


@pytest.mark.asyncio
async def test_manually_named_conversation_preserves_title(
    authenticated_client,
    mock_provider: MockTextGenerationProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={
            "title": "My project notes",
        },
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Help me organize this project.",
        },
    )

    assert response.status_code == 201, response.text

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200, detail.text
    assert detail.json()["title"] == "My project notes"

    assert len(mock_provider.assistant_requests) == 1
    assert len(mock_provider.title_requests) == 0


@pytest.mark.asyncio
async def test_provider_failure_does_not_save_messages(
    authenticated_client,
    mock_provider: MockTextGenerationProvider,
    mock_classifier: MockClassificationProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={
            "title": "Provider failure test",
        },
    )

    assert created.status_code == 201, created.text

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

    assert len(mock_classifier.requests) == 1
    assert len(mock_provider.assistant_requests) == 1
    assert mock_provider.title_requests == []


@pytest.mark.asyncio
async def test_send_conversation_message_requires_csrf(
    authenticated_client,
    mock_provider: MockTextGenerationProvider,
    mock_classifier: MockClassificationProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={
            "title": "CSRF test",
        },
    )

    assert created.status_code == 201, created.text

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

    assert mock_classifier.requests == []
    assert mock_provider.assistant_requests == []
    assert mock_provider.title_requests == []


@pytest.mark.asyncio
async def test_first_message_generates_title_through_api(
    authenticated_client,
    mock_provider: MockTextGenerationProvider,
    mock_classifier: MockClassificationProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={},
    )

    assert created.status_code == 201, created.text
    assert created.json()["title"] is None

    conversation_id = created.json()["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Help me understand my assignment.",
        },
    )

    assert response.status_code == 201, response.text
    assert len(response.json()) == 2

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200, detail.text

    assert detail.json()["title"] == ("Understanding Workplace Assignments")

    assert len(mock_classifier.requests) == 1
    assert len(mock_provider.assistant_requests) == 1
    assert len(mock_provider.title_requests) == 1

    title_request = mock_provider.title_requests[0]

    assert title_request.system_instructions is not None
    assert "Generate a short, descriptive title" in (title_request.system_instructions)


@pytest.mark.asyncio
async def test_disabled_capability_returns_409_without_saving_messages(
    authenticated_client,
    mock_provider: MockTextGenerationProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Disabled capability test"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    async def disabled_respond(
        self,
        message: str,
        history=None,
        classification=None,
    ):
        raise CapabilityDisabledError("No requested assistant capabilities are enabled")

    monkeypatch.setattr(
        AssistantOrchestrator,
        "respond",
        disabled_respond,
    )

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Break this assignment into steps.",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "This assistant capability is currently unavailable."}

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200
    assert detail.json()["messages"] == []
    assert mock_provider.assistant_requests == []
    assert mock_provider.title_requests == []


@pytest.mark.asyncio
async def test_classification_failure_returns_503_without_saving_messages(
    authenticated_client,
    mock_provider: MockTextGenerationProvider,
    mock_classifier: MockClassificationProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Classification failure test"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    async def invalid_classification(
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        mock_classifier.requests.append(request)

        return TextGenerationResponse(
            content="invalid JSON",
            model="mock-classifier",
        )

    monkeypatch.setattr(
        mock_classifier,
        "generate",
        invalid_classification,
    )

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Help me understand this assignment.",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": ("NeuroLens couldn't process your message. Please try again.")
    }

    assert len(mock_classifier.requests) == 2
    assert mock_provider.assistant_requests == []
    assert mock_provider.title_requests == []

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200
    assert detail.json()["messages"] == []


@pytest.mark.asyncio
async def test_unexpected_assistant_error_is_not_swallowed(
    authenticated_client,
    mock_provider: MockTextGenerationProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Unexpected error test"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    async def failing_respond(
        self,
        message: str,
        history=None,
        classification=None,
    ):
        raise RuntimeError("Unexpected internal failure")

    monkeypatch.setattr(
        AssistantOrchestrator,
        "respond",
        failing_respond,
    )

    with pytest.raises(
        RuntimeError,
        match="Unexpected internal failure",
    ):
        await client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={
                "content": "Explain this message.",
            },
        )

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200
    assert detail.json()["messages"] == []
    assert mock_provider.assistant_requests == []


@pytest.mark.asyncio
async def test_extract_tasks_from_selected_conversation_message(
    authenticated_client,
    mock_task_extraction: MockTaskExtractionProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Client feedback"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    sent = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": (
                "My manager said: Review last week's client feedback "
                "and prepare a summary for the team."
            ),
        },
    )

    assert sent.status_code == 201, sent.text

    source_message_id = sent.json()[0]["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages/{source_message_id}/extract-tasks",
    )

    assert response.status_code == 200, response.text

    tasks = response.json()["tasks"]

    assert len(tasks) == 1
    assert tasks[0]["title"] == "Review client feedback"
    assert tasks[0]["priority"] is None
    assert tasks[0]["source_text"] == ("Review last week's client feedback")

    assert len(mock_task_extraction.requests) == 1

    request = mock_task_extraction.requests[0]

    assert "Review last week's client feedback" in (request.messages[0].content)

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 2


@pytest.mark.asyncio
async def test_extract_tasks_from_earlier_conversation_message(
    authenticated_client,
    mock_classifier: MockClassificationProvider,
    mock_task_extraction: MockTaskExtractionProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Client feedback discussion"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    first = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": (
                "My manager asked me to Review last week's client feedback and prepare a summary."
            ),
        },
    )

    assert first.status_code == 201, first.text

    source_message_id = first.json()[0]["id"]

    async def resolve_source(
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        mock_classifier.requests.append(request)

        return TextGenerationResponse(
            content=json.dumps(
                {
                    "message_id": source_message_id,
                }
            ),
            model="mock-classifier",
        )

    monkeypatch.setattr(
        mock_classifier,
        "generate",
        resolve_source,
    )

    response = await client.post(
        f"/api/conversations/{conversation_id}/extract-tasks",
        json={
            "request": (
                "Can you extract the tasks from my manager's request we discussed earlier?"
            ),
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["source_message_id"] == source_message_id
    assert len(response.json()["tasks"]) == 1

    assert len(mock_task_extraction.requests) == 1

    extraction_request = mock_task_extraction.requests[0]

    assert "Review last week's client feedback" in (extraction_request.messages[0].content)

    assert "Can you extract the tasks" not in (extraction_request.messages[0].content)

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 2


@pytest.mark.asyncio
async def test_extract_tasks_rejects_nonexistent_message(
    authenticated_client,
    mock_task_extraction: MockTaskExtractionProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Missing source"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages/{uuid.uuid4()}/extract-tasks",
    )

    assert response.status_code == 404
    assert mock_task_extraction.requests == []


@pytest.mark.asyncio
async def test_extract_tasks_rejects_assistant_message(
    authenticated_client,
    mock_task_extraction: MockTaskExtractionProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Assistant source test"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    sent = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Review last week's client feedback.",
        },
    )

    assert sent.status_code == 201, sent.text

    assistant_message_id = sent.json()[1]["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages/{assistant_message_id}/extract-tasks",
    )

    assert response.status_code == 404
    assert mock_task_extraction.requests == []


@pytest.mark.asyncio
async def test_extract_tasks_requires_csrf(
    authenticated_client,
    mock_task_extraction: MockTaskExtractionProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Extraction CSRF test"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/extract-tasks",
        json={
            "request": "Extract tasks from the previous message.",
        },
        headers={
            "X-CSRF-Token": "",
        },
    )

    assert response.status_code == 403
    assert mock_task_extraction.requests == []


@pytest.mark.asyncio
async def test_task_extraction_provider_failure_returns_503(
    authenticated_client,
    mock_task_extraction: MockTaskExtractionProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Extraction failure test"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    sent = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Review last week's client feedback.",
        },
    )

    assert sent.status_code == 201, sent.text

    source_message_id = sent.json()[0]["id"]

    mock_task_extraction.should_fail = True

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages/{source_message_id}/extract-tasks",
    )

    assert response.status_code == 503
    assert "Internal extraction provider details" not in response.text

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 2


@pytest.mark.asyncio
async def test_invalid_task_extraction_returns_503(
    authenticated_client,
    mock_task_extraction: MockTaskExtractionProvider,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Invalid extraction test"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    sent = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Review last week's client feedback.",
        },
    )

    assert sent.status_code == 201, sent.text

    source_message_id = sent.json()[0]["id"]

    mock_task_extraction.invalid_json = True

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages/{source_message_id}/extract-tasks",
    )

    assert response.status_code == 503

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 2


@pytest.mark.asyncio
async def test_ambiguous_task_source_returns_409_without_saving_messages(
    authenticated_client,
    mock_classifier: MockClassificationProvider,
    mock_provider: MockTextGenerationProvider,
    mock_task_extraction: MockTaskExtractionProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Ambiguous extraction"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    async def classify_extraction(
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        mock_classifier.requests.append(request)

        return TextGenerationResponse(
            content=json.dumps(
                {
                    "intents": [
                        {
                            "capability": "task_extraction",
                            "instruction": "Extract earlier tasks.",
                            "source_text": None,
                        }
                    ]
                }
            ),
            model="mock-classifier",
        )

    monkeypatch.setattr(
        mock_classifier,
        "generate",
        classify_extraction,
    )

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Extract the tasks from that earlier request.",
        },
    )

    assert response.status_code == 409

    assert "couldn't determine which earlier message" in (response.json()["detail"])

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200
    assert detail.json()["messages"] == []

    assert mock_provider.assistant_requests == []
    assert mock_task_extraction.requests == []


@pytest.mark.asyncio
async def test_chat_task_suggestions_survive_conversation_reload(
    authenticated_client,
    mock_classifier: MockClassificationProvider,
    mock_task_extraction: MockTaskExtractionProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Task extraction persistence"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    source_response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": (
                "My manager asked me to Review last week's client feedback and prepare a summary."
            ),
        },
    )

    assert source_response.status_code == 201, source_response.text

    source_message_id = source_response.json()[0]["id"]

    async def classify_or_resolve(
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        mock_classifier.requests.append(request)

        instructions = request.system_instructions or ""

        if "Identify the earlier employee-provided message" in instructions:
            return TextGenerationResponse(
                content=json.dumps(
                    {
                        "message_id": source_message_id,
                    }
                ),
                model="mock-classifier",
            )

        return TextGenerationResponse(
            content=json.dumps(
                {
                    "intents": [
                        {
                            "capability": "task_extraction",
                            "instruction": (
                                "Extract task suggestions from the earlier manager request."
                            ),
                            "source_text": None,
                        }
                    ]
                }
            ),
            model="mock-classifier",
        )

    monkeypatch.setattr(
        mock_classifier,
        "generate",
        classify_or_resolve,
    )

    extraction_response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": ("Extract the tasks from my manager's request we discussed earlier."),
        },
    )

    assert extraction_response.status_code == 201, extraction_response.text

    assistant_message = extraction_response.json()[1]

    assert assistant_message["role"] == "assistant"

    suggestions = assistant_message["task_suggestions"]

    assert suggestions is not None
    assert suggestions["source_message_id"] == source_message_id
    assert len(suggestions["tasks"]) == 1
    assert suggestions["tasks"][0]["title"] == "Review client feedback"

    assert len(mock_task_extraction.requests) == 1

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200, detail.text

    stored_messages = detail.json()["messages"]

    assert len(stored_messages) == 4

    restored_suggestions = stored_messages[-1]["task_suggestions"]

    assert restored_suggestions == suggestions

    assert stored_messages[0]["task_suggestions"] is None
    assert stored_messages[1]["task_suggestions"] is None
    assert stored_messages[2]["task_suggestions"] is None


@pytest.mark.asyncio
async def test_cannot_extract_tasks_from_another_employees_conversation(
    authenticated_client,
    test_session_factory: async_sessionmaker[AsyncSession],
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    mock_classifier: MockClassificationProvider,
    mock_task_extraction: MockTaskExtractionProvider,
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
            service = ConversationService(
                db=db,
                session_factory=test_session_factory,
            )

            conversation = await service.create(
                employee_id=other_employee_id,
                title="Private manager assignment",
            )

            conversation_id = conversation.id

        direct_response = await client.post(
            f"/api/conversations/{conversation_id}/messages/{uuid.uuid4()}/extract-tasks",
        )

        historical_response = await client.post(
            f"/api/conversations/{conversation_id}/extract-tasks",
            json={
                "request": "Extract tasks from the earlier manager message.",
            },
        )

        chat_response = await client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={
                "content": "Extract tasks from the earlier manager message.",
            },
        )

        assert direct_response.status_code == 404
        assert historical_response.status_code == 404
        assert chat_response.status_code == 404

        # Unauthorized requests must never reach an AI provider.
        assert mock_classifier.requests == []
        assert mock_task_extraction.requests == []

    finally:
        async with test_admin_session_factory() as db:
            await db.execute(
                delete(Employee).where(
                    Employee.user_id == other_employee_id,
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_task_source_resolver_rejects_fabricated_message_id(
    authenticated_client,
    mock_classifier: MockClassificationProvider,
    mock_task_extraction: MockTaskExtractionProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = authenticated_client

    created = await client.post(
        "/api/conversations",
        json={"title": "Invalid task source"},
    )

    assert created.status_code == 201, created.text

    conversation_id = created.json()["id"]

    source_response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": (
                "My manager asked me to review last week's client feedback and prepare a summary."
            ),
        },
    )

    assert source_response.status_code == 201, source_response.text

    fabricated_id = str(uuid.uuid4())

    async def classify_or_resolve(
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        mock_classifier.requests.append(request)

        instructions = request.system_instructions or ""

        if "Identify the earlier employee-provided message" in instructions:
            return TextGenerationResponse(
                content=json.dumps(
                    {
                        "message_id": fabricated_id,
                    }
                ),
                model="mock-classifier",
            )

        return TextGenerationResponse(
            content=json.dumps(
                {
                    "intents": [
                        {
                            "capability": "task_extraction",
                            "instruction": ("Extract tasks from the earlier manager request."),
                            "source_text": None,
                        }
                    ]
                }
            ),
            model="mock-classifier",
        )

    monkeypatch.setattr(
        mock_classifier,
        "generate",
        classify_or_resolve,
    )

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": ("Extract the tasks from the manager's request we discussed earlier."),
        },
    )

    assert response.status_code == 503
    assert "fabricated_id" not in response.text
    assert fabricated_id not in response.text

    assert mock_task_extraction.requests == []

    detail = await client.get(f"/api/conversations/{conversation_id}")

    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 2
