import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.ai.capabilities.types import AICapability
from app.models.employee_profile import EmployeeProfile
from app.services.assistant_config import AssistantConfig
from app.services.assistant_orchestrator import AssistantOrchestrator
from tests.helpers.mock_ai_registry import create_mock_ai_registry


@pytest.mark.asyncio
async def test_message_explanation_uses_registered_provider(
    employee_client: AsyncClient,
    mock_ai_registry,
) -> None:
    registry, providers = mock_ai_registry

    response = await employee_client.post(
        "/api/assistant/messages",
        json={
            "message": "Explain what my manager means by EOD.",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["content"] == ("Your manager is requesting an update.")
    assert data["model"] == "mock-model"

    assert len(providers[AICapability.REQUEST_CLASSIFICATION].requests) == 1

    assert len(providers[AICapability.MESSAGE_EXPLANATION].requests) == 1


@pytest.mark.asyncio
async def test_employee_preferences_reach_explanation_provider(
    employee_client: AsyncClient,
    mock_ai_registry,
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    _, providers = mock_ai_registry

    async with test_session_factory() as db:
        profile = await db.scalar(
            select(EmployeeProfile).where(
                EmployeeProfile.user_id == employee_id,
            )
        )

        if profile is None:
            profile = EmployeeProfile(user_id=employee_id)
            db.add(profile)

        profile.directness = "high"
        profile.response_length = "short"
        profile.highlight_ambiguity = False
        profile.step_by_step_guidance = False
        profile.always_show_next_step = False

        await db.commit()

    response = await employee_client.post(
        "/api/assistant/messages",
        json={
            "message": "Explain what my manager means by EOD.",
        },
    )

    assert response.status_code == 200, response.text

    explanation_provider = providers[AICapability.MESSAGE_EXPLANATION]

    assert len(explanation_provider.requests) == 1

    instructions = explanation_provider.requests[0].system_instructions

    assert instructions is not None
    assert "Be direct" in instructions
    assert "Keep responses brief" in instructions
    assert "Prefer short paragraphs" in instructions
    assert "Do not automatically append" in instructions


@pytest.mark.asyncio
async def test_disabled_task_assistance_does_not_call_provider() -> None:
    registry, providers = create_mock_ai_registry()

    providers[AICapability.REQUEST_CLASSIFICATION].content = (
        '{"intents": ['
        '{"capability": "task_assistance", '
        '"instruction": "Break down this assignment.", '
        '"source_text": null}'
        "]}"
    )

    orchestrator = AssistantOrchestrator(
        registry=registry,
        config=AssistantConfig(
            enable_task_assistance=False,
        ),
    )

    results = await orchestrator.respond("Break down this assignment into steps.")

    assert results == []

    assert len(providers[AICapability.TASK_ASSISTANCE].requests) == 0


@pytest.mark.asyncio
async def test_conversation_persists_orchestrated_messages(
    employee_client: AsyncClient,
    mock_ai_registry,
) -> None:
    _, providers = mock_ai_registry

    create_response = await employee_client.post(
        "/api/conversations",
        json={"title": None},
    )

    assert create_response.status_code == 201, create_response.text

    conversation_id = create_response.json()["id"]

    message_response = await employee_client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Explain what my manager means by EOD.",
        },
    )

    assert message_response.status_code == 201, message_response.text

    messages = message_response.json()

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == ("Explain what my manager means by EOD.")

    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == ("Your manager is requesting an update.")
    assert messages[1]["model"] == "mock-model"

    detail_response = await employee_client.get(
        f"/api/conversations/{conversation_id}",
    )

    assert detail_response.status_code == 200, detail_response.text

    stored_messages = detail_response.json()["messages"]

    assert len(stored_messages) == 2
    assert [message["role"] for message in stored_messages] == [
        "user",
        "assistant",
    ]

    assert len(providers[AICapability.REQUEST_CLASSIFICATION].requests) == 1

    assert len(providers[AICapability.MESSAGE_EXPLANATION].requests) == 1


@pytest.mark.asyncio
async def test_conversation_uses_dedicated_title_provider(
    employee_client: AsyncClient,
    mock_ai_registry,
) -> None:
    _, providers = mock_ai_registry

    create_response = await employee_client.post(
        "/api/conversations",
        json={"title": None},
    )

    assert create_response.status_code == 201, create_response.text

    conversation_id = create_response.json()["id"]

    first_response = await employee_client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Help me understand my manager's message.",
        },
    )

    assert first_response.status_code == 201, first_response.text

    detail_response = await employee_client.get(
        f"/api/conversations/{conversation_id}",
    )

    assert detail_response.status_code == 200, detail_response.text

    assert detail_response.json()["title"] == ("Understanding Workplace Messages")

    title_provider = providers[AICapability.CONVERSATION_TITLE]

    explanation_provider = providers[AICapability.MESSAGE_EXPLANATION]

    assert len(title_provider.requests) == 1
    assert len(explanation_provider.requests) == 1

    title_request = title_provider.requests[0]

    assert title_request.system_instructions is not None
    assert "Generate a short, descriptive title" in title_request.system_instructions

    second_response = await employee_client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Can you explain it again?",
        },
    )

    assert second_response.status_code == 201, second_response.text

    # Follow-up messages must not regenerate the conversation title.
    assert len(title_provider.requests) == 1


@pytest.mark.asyncio
async def test_conversation_preserves_follow_up_messages(
    employee_client: AsyncClient,
    mock_ai_registry,
) -> None:
    _, providers = mock_ai_registry

    create_response = await employee_client.post(
        "/api/conversations",
        json={"title": None},
    )

    assert create_response.status_code == 201, create_response.text

    conversation_id = create_response.json()["id"]

    messages_to_send = [
        "Explain what EOD means.",
        "What does that imply for my work?",
        "Can you make the explanation clearer?",
    ]

    for content in messages_to_send:
        response = await employee_client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"content": content},
        )

        assert response.status_code == 201, response.text

    detail_response = await employee_client.get(
        f"/api/conversations/{conversation_id}",
    )

    assert detail_response.status_code == 200, detail_response.text

    messages = detail_response.json()["messages"]

    assert len(messages) == 6

    assert [message["role"] for message in messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
        "assistant",
    ]

    assert [
        message["content"] for message in messages if message["role"] == "user"
    ] == messages_to_send

    assert len(providers[AICapability.REQUEST_CLASSIFICATION].requests) == 3

    assert len(providers[AICapability.MESSAGE_EXPLANATION].requests) == 3

    # History is persisted, but classified generation currently
    # uses capability-scoped requests rather than prior chat turns.
    for request in providers[AICapability.MESSAGE_EXPLANATION].requests:
        assert len(request.messages) == 1


@pytest.mark.asyncio
async def test_policy_question_uses_referral_without_generation(
    employee_client: AsyncClient,
    mock_ai_registry,
) -> None:
    _, providers = mock_ai_registry

    providers[AICapability.REQUEST_CLASSIFICATION].content = json.dumps(
        {
            "intents": [
                {
                    "capability": "policy_question",
                    "instruction": ("Identify the annual leave entitlement question."),
                    "source_text": None,
                },
            ],
        }
    )

    create_response = await employee_client.post(
        "/api/conversations",
        json={"title": None},
    )

    assert create_response.status_code == 201, create_response.text

    conversation_id = create_response.json()["id"]

    response = await employee_client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "How many annual leave days do I receive?",
        },
    )

    assert response.status_code == 201, response.text

    messages = response.json()

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

    assert "can't verify" in messages[1]["content"]

    assert len(providers[AICapability.MESSAGE_EXPLANATION].requests) == 0

    assert len(providers[AICapability.TASK_ASSISTANCE].requests) == 0

    assert len(providers[AICapability.GENERAL_CONVERSATION].requests) == 0

    assert len(
        providers[AICapability.CONVERSATION_TITLE].requests
    ) == 1

    detail_response = await employee_client.get(
        f"/api/conversations/{conversation_id}",
    )

    assert detail_response.status_code == 200, detail_response.text
    assert len(detail_response.json()["messages"]) == 2
