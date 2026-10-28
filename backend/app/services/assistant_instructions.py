from app.services.assistant_config import AssistantConfig


def build_preference_instructions(
    config: AssistantConfig,
) -> str:
    directness = {
        "low": (
            "Use a gentle, considerate tone. Be clear without sounding abrupt or overly formal."
        ),
        "balanced": (
            "Use a clear, approachable, and professional tone. "
            "Be friendly without unnecessary reassurance or filler."
        ),
        "high": (
            "Be direct, explicit, and concise. Lead with the "
            "important information and avoid unnecessary introductions."
        ),
    }

    response_length = {
        "short": (
            "Prefer 1 to 2 concise sentences for simple explanations. "
            "When actions are requested, usually give no more than "
            "2 practical steps. Include additional detail only when essential."
        ),
        "medium": (
            "For straightforward explanations, prefer 2 to 4 sentences. "
            "When actions are requested, usually provide 2 to 4 "
            "practical steps. Avoid excessive sections and repetition."
        ),
        "detailed": (
            "Provide a thorough but well-organized response. "
            "Include relevant context, dependencies, and important "
            "uncertainties when useful. Avoid unnecessary repetition."
        ),
    }

    instructions = [
        "Employee communication preferences:",
        directness[config.directness],
        response_length[config.response_length],
    ]

    if config.highlight_ambiguity:
        instructions.append(
            "Identify ambiguity only when it could change the "
            "employee's understanding or next action. "
            "Prefer a brief clarification over a long list of unknowns."
        )
    else:
        instructions.append(
            "Do not include a separate ambiguity section by default. "
            "Still communicate uncertainty when necessary for accuracy."
        )

    if config.step_by_step_guidance:
        instructions.append(
            "When actionable guidance is needed, present a short, "
            "ordered sequence of manageable steps. "
            "Do not invent extra work simply to create more steps."
        )
    else:
        instructions.append(
            "Prefer concise, natural-language guidance rather than "
            "numbered steps, unless the employee explicitly asks "
            "for a task breakdown or checklist."
        )

    if config.always_show_next_step:
        instructions.append(
            "When an actionable next step exists and has not already "
            "been made clear, suggest one specific next action. "
            "Do not repeat an existing plan or invent obligations."
        )
    else:
        instructions.append(
            "Do not automatically append a next-step recommendation "
            "unless explicitly requested or essential to the answer."
        )

    instructions.append(
        "Treat these preferences as communication guidance. "
        "Never compromise factual accuracy, important uncertainty, "
        "or organizational capability restrictions to follow them."
    )

    return "\n".join(instructions)
