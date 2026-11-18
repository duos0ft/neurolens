from app.services.assistant.assistant_config import AssistantConfig
from app.services.assistant.assistant_instructions import build_preference_instructions


def test_default_preferences() -> None:
    instructions = build_preference_instructions(AssistantConfig())

    assert "clear, approachable, and professional tone" in instructions
    assert "2 to 4 sentences" in instructions
    assert "manageable actions" in instructions
    assert "identify one specific, realistic next action" in instructions


def test_direct_and_short_responses() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            directness="high",
            response_length="short",
        )
    )

    assert "Be direct, explicit, and concise" in instructions
    assert "1 to 2 sentences" in instructions
    assert "1 to 2 manageable steps" in instructions
    assert "Never omit essential" in instructions


def test_disabling_step_by_step_guidance() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            step_by_step_guidance=False,
        )
    )

    assert "Prefer concise natural-language explanations" in instructions
    assert "If the employee explicitly requests procedural guidance" in instructions
    assert "provide it despite this preference being disabled" in instructions
    assert "Do not prevent the dedicated task-extraction workflow" in instructions


def test_disabling_ambiguity_highlighting() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            highlight_ambiguity=False,
        )
    )

    assert "Do not proactively add ambiguity analysis" in instructions
    assert "Still communicate uncertainty" in instructions
    assert "avoid misleading the employee" in instructions


def test_disabling_next_step_suggestions() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            always_show_next_step=False,
        )
    )

    assert "Do not automatically append a next-step recommendation" in instructions
    assert "when the employee explicitly" in instructions


def test_medium_response_preferences_are_proportionate() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            response_length="medium",
        )
    )

    assert "2 to 4 sentences" in instructions
    assert "2 to 4 manageable steps" in instructions
    assert "Avoid repetition" in instructions


def test_detailed_response_still_avoids_repetition() -> None:
    instructions = build_preference_instructions(
        AssistantConfig(
            response_length="detailed",
        )
    )

    assert "thorough but well-organized responses" in instructions
    assert "relevant context" in instructions
    assert "Use headings" in instructions
    assert "only when they improve readability" in instructions


def test_enabled_and_disabled_step_guidance_are_distinct() -> None:
    enabled = build_preference_instructions(
        AssistantConfig(
            step_by_step_guidance=True,
        )
    )

    disabled = build_preference_instructions(
        AssistantConfig(
            step_by_step_guidance=False,
        )
    )

    assert "provide a short, ordered breakdown" in enabled
    assert "Prefer concise natural-language explanations" in disabled
    assert enabled != disabled


def test_enabled_and_disabled_ambiguity_guidance_are_distinct() -> None:
    enabled = build_preference_instructions(
        AssistantConfig(
            highlight_ambiguity=True,
        )
    )

    disabled = build_preference_instructions(
        AssistantConfig(
            highlight_ambiguity=False,
        )
    )

    assert "proactively identify missing" in enabled
    assert "Do not proactively add ambiguity analysis" in disabled
    assert enabled != disabled


def test_enabled_and_disabled_next_step_guidance_are_distinct() -> None:
    enabled = build_preference_instructions(
        AssistantConfig(
            always_show_next_step=True,
        )
    )

    disabled = build_preference_instructions(
        AssistantConfig(
            always_show_next_step=False,
        )
    )

    assert "identify one specific, realistic next action" in enabled
    assert "Do not automatically append a next-step recommendation" in disabled
    assert enabled != disabled
