from app.schemas.employee import (
    CommunicationPreferences,
    DirectnessLevel,
    EmployeeProfile,
    ResponseLength,
)


def test_default_communication_preferences() -> None:
    profile = EmployeeProfile()

    assert profile.preferences.directness == DirectnessLevel.BALANCED
    assert profile.preferences.response_length == ResponseLength.MEDIUM
    assert profile.preferences.highlight_ambiguity is True
    assert profile.preferences.step_by_step_guidance is True
    assert profile.preferences.always_show_next_step is True


def test_custom_communication_preferences() -> None:
    preferences = CommunicationPreferences(
        directness=DirectnessLevel.HIGH,
        response_length=ResponseLength.SHORT,
        highlight_ambiguity=True,
        step_by_step_guidance=False,
        always_show_next_step=True,
    )

    assert preferences.directness == DirectnessLevel.HIGH
    assert preferences.response_length == ResponseLength.SHORT
