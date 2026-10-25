from app.services.assistant_config import AssistantConfig
from app.services.assistant_instructions import build_preference_instructions


def test_default_preferences() -> None:
    instructions = build_preference_instructions(AssistantConfig())

    assert "balanced" in instructions
    assert "manageable steps" in instructions
    assert "make it explicit" in instructions


def test_direct_and_short_responses() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            directness="high",
            response_length="short",
        )
    )

    assert "Be direct" in instructions
    assert "Keep responses brief" in instructions


def test_disabling_step_by_step_guidance() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            step_by_step_guidance=False,
        )
    )

    assert "Prefer short paragraphs" in instructions


def test_disabling_ambiguity_highlighting() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            highlight_ambiguity=False,
        )
    )

    assert "Do not add a separate ambiguity section" in instructions
    assert "Still identify uncertainty" in instructions


def test_disabling_next_step_suggestions() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            always_show_next_step=False,
        )
    )

    assert "Do not automatically append" in instructions