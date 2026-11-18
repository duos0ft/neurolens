import json
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.capabilities.text_generation import (
    TextGenerationError,
    TextGenerationRequest,
    TextGenerationResponse,
)
from app.ai.capabilities.types import AICapability
from app.ai.registry import AIProviderRegistry
from app.api.assistant_dependencies import get_ai_provider_registry
from app.core.database import get_db
from app.core.settings import settings
from app.main import create_app
from app.models.employee import Employee
from app.models.employee_session import EmployeeSession
from app.services.authentication.oauth import generate_token, hash_token


class MockTextGenerationProvider:
    def __init__(self) -> None:
        self.last_request: TextGenerationRequest | None = None

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        self.last_request = request

        return TextGenerationResponse(
            content=json.dumps(
                {
                    "explanation": "Break the assignment into three manageable steps.",
                    "ambiguities": [],
                    "steps": [],
                    "next_step": None,
                }
            ),
            model="mock-model",
        )


class MockClassificationProvider:
    def __init__(self) -> None:
        self.last_request: TextGenerationRequest | None = None

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        self.last_request = request

        return TextGenerationResponse(
            content=json.dumps(
                {
                    "intents": [
                        {
                            "capability": "message_explanation",
                            "instruction": "Explain the employee request.",
                            "source_text": None,
                        },
                    ],
                }
            ),
            model="mock-classifier",
        )


@pytest.fixture
async def authenticated_client(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> AsyncIterator[
    tuple[
        httpx.AsyncClient,
        MockTextGenerationProvider,
        MockClassificationProvider,
    ]
]:
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

    provider = MockTextGenerationProvider()
    classifier = MockClassificationProvider()

    registry = AIProviderRegistry()

    registry.register_text_generation(
        AICapability.REQUEST_CLASSIFICATION,
        classifier,
    )

    registry.register_text_generation(
        AICapability.MESSAGE_EXPLANATION,
        provider,
    )

    app = create_app()

    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
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

            yield client, provider, classifier

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_authenticated_employee_can_send_message(
    authenticated_client,
) -> None:
    client, provider, classifier = authenticated_client

    response = await client.post(
        "/api/assistant/messages",
        json={
            "message": "Help me understand this assignment.",
        },
    )

    assert response.status_code == 200, response.text

    assert response.json() == {
        "content": "Break the assignment into three manageable steps.",
        "model": "mock-model",
    }

    assert classifier.last_request is not None
    assert provider.last_request is not None

    assert provider.last_request.messages[0].role == "user"

    assert "Help me understand this assignment." in (provider.last_request.messages[0].content)

    assert "Explain the employee request." in (provider.last_request.messages[0].content)

    assert provider.last_request.system_instructions is not None

    assert "Explain the central meaning in plain, natural language" in (
        provider.last_request.system_instructions
    )

    assert "Structured explanation output:" in (provider.last_request.system_instructions)

    # The API must expose the composed explanation, not raw JSON.
    assert not response.json()["content"].startswith("{")
    assert '"ambiguities":' not in response.json()["content"]


@pytest.mark.asyncio
async def test_assistant_rejects_empty_message(
    authenticated_client,
) -> None:
    client, provider, classifier = authenticated_client

    response = await client.post(
        "/api/assistant/messages",
        json={
            "message": "   ",
        },
    )

    assert response.status_code == 422
    assert provider.last_request is None
    assert classifier.last_request is None


@pytest.mark.asyncio
async def test_assistant_requires_csrf(
    authenticated_client,
) -> None:
    client, provider, classifier = authenticated_client

    response = await client.post(
        "/api/assistant/messages",
        json={
            "message": "Explain these instructions.",
        },
        headers={
            "X-CSRF-Token": "",
        },
    )

    assert response.status_code == 403
    assert provider.last_request is None
    assert classifier.last_request is None


@pytest.mark.asyncio
async def test_assistant_handles_provider_failure(
    authenticated_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, provider, classifier = authenticated_client

    async def failing_generate(
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        raise TextGenerationError("Internal provider connection details")

    monkeypatch.setattr(
        provider,
        "generate",
        failing_generate,
    )

    response = await client.post(
        "/api/assistant/messages",
        json={
            "message": "Help me understand this assignment.",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "The AI assistant is temporarily unavailable",
    }

    assert "Internal provider connection details" not in response.text
    assert classifier.last_request is not None


@pytest.mark.asyncio
async def test_unauthenticated_employee_cannot_send_message(
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
            headers={
                "Origin": settings.frontend_url,
            },
        ) as client:
            response = await client.post(
                "/api/assistant/messages",
                json={
                    "message": "Help me understand this task.",
                },
            )

        assert response.status_code == 401

    finally:
        app.dependency_overrides.clear()
