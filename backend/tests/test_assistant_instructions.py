from app.services.assistant_config import AssistantConfig
from app.services.assistant_instructions import build_preference_instructions


def test_default_preferences() -> None:
    instructions = build_preference_instructions(AssistantConfig())

    assert "clear, approachable, and professional tone" in instructions
    assert "2 to 4 sentences" in instructions
    assert "manageable steps" in instructions
    assert "one specific next action" in instructions


def test_direct_and_short_responses() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            directness="high",
            response_length="short",
        )
    )

    assert "Be direct, explicit, and concise" in instructions
    assert "1 to 2 concise sentences" in instructions
    assert "2 practical steps" in instructions


def test_disabling_step_by_step_guidance() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            step_by_step_guidance=False,
        )
    )

    assert "concise, natural-language guidance" in instructions
    assert "unless the employee explicitly asks" in instructions


def test_disabling_ambiguity_highlighting() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            highlight_ambiguity=False,
        )
    )

    assert "Do not include a separate ambiguity section" in instructions
    assert "Still communicate uncertainty" in instructions


def test_disabling_next_step_suggestions() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            always_show_next_step=False,
        )
    )

    assert "Do not automatically append a next-step recommendation" in instructions


def test_medium_response_preferences_are_proportionate() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            response_length="medium",
        )
    )

    assert "2 to 4 sentences" in instructions
    assert "2 to 4" in instructions
    assert "practical steps" in instructions
    assert "Avoid excessive sections" in instructions


def test_detailed_response_still_avoids_repetition() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            response_length="detailed",
        )
    )

    assert "thorough" in instructions
    assert "Avoid unnecessary repetition" in instructions
