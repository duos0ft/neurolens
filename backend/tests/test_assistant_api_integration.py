import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.capabilities.types import AICapability
from app.models.employee_profile import EmployeeProfile
from app.services.assistant_config import AssistantConfig
from app.services.assistant_orchestrator import (
    AssistantOrchestrator,
    CapabilityDisabledError,
)
from tests.helpers.mock_ai_registry import create_mock_ai_registry


EXPLANATION_CONTENT = "Your manager is requesting an update."


@pytest.fixture
def structured_mock_ai_registry(mock_ai_registry):
    registry, providers = mock_ai_registry

    providers[AICapability.MESSAGE_EXPLANATION].content = json.dumps(
        {
            "explanation": EXPLANATION_CONTENT,
            "ambiguities": [],
            "steps": [],
            "next_step": None,
        }
    )

    return registry, providers


@pytest.mark.asyncio
async def test_message_explanation_uses_registered_provider(
    employee_client: AsyncClient,
    structured_mock_ai_registry,
) -> None:
    registry, providers = structured_mock_ai_registry

    response = await employee_client.post(
        "/api/assistant/messages",
        json={
            "message": "Explain what my manager means by EOD.",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["content"] == EXPLANATION_CONTENT
    assert data["model"] == "mock-model"

    assert not data["content"].startswith("{")

    assert len(providers[AICapability.REQUEST_CLASSIFICATION].requests) == 1

    assert len(providers[AICapability.MESSAGE_EXPLANATION].requests) == 1

    explanation_request = providers[AICapability.MESSAGE_EXPLANATION].requests[0]

    assert explanation_request.system_instructions is not None

    assert "Structured explanation output:" in (explanation_request.system_instructions)


@pytest.mark.asyncio
async def test_employee_preferences_reach_explanation_provider(
    employee_client: AsyncClient,
    structured_mock_ai_registry,
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id
    _, providers = structured_mock_ai_registry

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
    assert response.json()["content"] == EXPLANATION_CONTENT

    explanation_provider = providers[AICapability.MESSAGE_EXPLANATION]

    assert len(explanation_provider.requests) == 1

    instructions = explanation_provider.requests[0].system_instructions

    assert instructions is not None
    assert "Be direct, explicit, and concise" in instructions
    assert "1 to 2 sentences" in instructions
    assert "Prefer concise natural-language explanations" in instructions
    assert "Do not proactively add ambiguity analysis" in instructions
    assert "Do not automatically append a next-step recommendation" in instructions

    assert "Structured explanation output:" in instructions


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

    with pytest.raises(
        CapabilityDisabledError,
        match="No requested assistant capabilities are enabled",
    ):
        await orchestrator.respond("Break down this assignment into steps.")

    assert len(providers[AICapability.TASK_ASSISTANCE].requests) == 0


@pytest.mark.asyncio
async def test_conversation_persists_orchestrated_messages(
    employee_client: AsyncClient,
    structured_mock_ai_registry,
) -> None:
    _, providers = structured_mock_ai_registry

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
    assert messages[1]["content"] == EXPLANATION_CONTENT
    assert messages[1]["model"] == "mock-model"

    assert not messages[1]["content"].startswith("{")

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

    assert stored_messages[1]["content"] == EXPLANATION_CONTENT

    assert len(providers[AICapability.REQUEST_CLASSIFICATION].requests) == 1

    assert len(providers[AICapability.MESSAGE_EXPLANATION].requests) == 1


@pytest.mark.asyncio
async def test_conversation_uses_dedicated_title_provider(
    employee_client: AsyncClient,
    structured_mock_ai_registry,
) -> None:
    _, providers = structured_mock_ai_registry

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

    assert first_response.json()[1]["content"] == EXPLANATION_CONTENT

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
    assert "Generate a short, descriptive title" in (title_request.system_instructions)

    second_response = await employee_client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "content": "Can you explain it again?",
        },
    )

    assert second_response.status_code == 201, second_response.text

    assert second_response.json()[1]["content"] == EXPLANATION_CONTENT

    # Follow-up messages must not regenerate the conversation title.
    assert len(title_provider.requests) == 1
    assert len(explanation_provider.requests) == 2


@pytest.mark.asyncio
async def test_conversation_preserves_follow_up_messages(
    employee_client: AsyncClient,
    structured_mock_ai_registry,
) -> None:
    _, providers = structured_mock_ai_registry

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

    assert all(
        message["content"] == EXPLANATION_CONTENT
        for message in messages
        if message["role"] == "assistant"
    )

    assert len(providers[AICapability.REQUEST_CLASSIFICATION].requests) == 3

    explanation_requests = providers[AICapability.MESSAGE_EXPLANATION].requests

    assert len(explanation_requests) == 3

    # First message: no previous conversation history.
    assert len(explanation_requests[0].messages) == 1

    # Second message: previous user/assistant exchange + current request.
    assert len(explanation_requests[1].messages) == 3

    assert [message.role for message in explanation_requests[1].messages] == [
        "user",
        "assistant",
        "user",
    ]

    assert explanation_requests[1].messages[0].content == ("Explain what EOD means.")

    assert explanation_requests[1].messages[1].content == (EXPLANATION_CONTENT)

    assert "What does that imply for my work?" in (explanation_requests[1].messages[2].content)

    # Third message: two previous exchanges + current request.
    assert len(explanation_requests[2].messages) == 5

    assert [message.role for message in explanation_requests[2].messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
    ]

    assert "Can you make the explanation clearer?" in (explanation_requests[2].messages[-1].content)


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

    assert len(
        providers[AICapability.GENERAL_CONVERSATION].requests
    ) == 0

    assert len(
        providers[AICapability.CONVERSATION_TITLE].requests
    ) == 1

    detail_response = await employee_client.get(
        f"/api/conversations/{conversation_id}",
    )

    assert detail_response.status_code == 200, detail_response.text
    assert len(detail_response.json()["messages"]) == 2
