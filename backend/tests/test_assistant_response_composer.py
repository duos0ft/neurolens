from app.ai.capabilities.text_generation import TextGenerationResponse
from app.ai.capabilities.types import AICapability
from app.services.assistant_orchestrator import CapabilityResult
from app.services.assistant_response_composer import AssistantResponseComposer


def test_composes_multiple_capabilities() -> None:
    composer = AssistantResponseComposer()

    response = composer.compose(
        [
            CapabilityResult(
                capability=AICapability.MESSAGE_EXPLANATION,
                response=TextGenerationResponse(
                    content="Your manager is requesting a progress update.",
                    model="explanation-model",
                ),
            ),
            CapabilityResult(
                capability=AICapability.TASK_ASSISTANCE,
                response=TextGenerationResponse(
                    content="1. Check progress.\n2. Report blockers.",
                    model="task-model",
                ),
            ),
        ]
    )

    assert "### What this means" in response.content
    assert "### What to do" in response.content
    assert "Your manager is requesting a progress update." in response.content
    assert "1. Check progress." in response.content
    assert response.model == "neurolens-composed"


def test_preserves_single_provider_response() -> None:
    composer = AssistantResponseComposer()

    response = composer.compose(
        [
            CapabilityResult(
                capability=AICapability.MESSAGE_EXPLANATION,
                response=TextGenerationResponse(
                    content="EOD means end of day.",
                    model="explanation-model",
                ),
            ),
        ]
    )

    assert response.content == "EOD means end of day."
    assert response.model == "explanation-model"


def test_returns_clarification_for_empty_results() -> None:
    composer = AssistantResponseComposer()

    response = composer.compose([])

    assert "Could you clarify" in response.content
    assert response.model == "neurolens"
