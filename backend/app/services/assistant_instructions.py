from app.services.assistant_config import AssistantConfig


def build_preference_instructions(
    config: AssistantConfig,
) -> str:
    instructions = [
        "Employee communication preferences:",
    ]

    directness = {
        "low": ("Use a gentle, considerate tone while remaining clear and specific."),
        "balanced": ("Use a balanced, professional, and approachable tone."),
        "high": ("Be direct, explicit, and concise. Avoid unnecessary introductions."),
    }

    instructions.append(directness[config.directness])

    response_length = {
        "short": ("Keep responses brief and include only essential details."),
        "medium": (
            "Provide enough detail to explain the request clearly without unnecessary elaboration."
        ),
        "detailed": (
            "Provide thorough explanations when additional detail "
            "helps the employee understand the request."
        ),
    }

    instructions.append(response_length[config.response_length])

    if config.highlight_ambiguity:
        instructions.append(
            "Explicitly identify important ambiguity, missing "
            "information, and uncertain interpretations."
        )
    else:
        instructions.append(
            "Do not add a separate ambiguity section by default. "
            "Still identify uncertainty when necessary to avoid "
            "misleading the employee."
        )

    if config.step_by_step_guidance:
        instructions.append(
            "When providing actionable guidance, organize it "
            "into clear, manageable steps when useful."
        )
    else:
        instructions.append(
            "Prefer short paragraphs over numbered steps, "
            "unless the employee explicitly requests a checklist "
            "or step-by-step instructions."
        )

    if config.always_show_next_step:
        instructions.append(
            "When a meaningful next step exists, make it explicit. "
            "Do not invent responsibilities or deadlines."
        )
    else:
        instructions.append(
            "Do not automatically append a next-step suggestion "
            "unless the employee requests one or it is essential."
        )

    return "\n".join(instructions)