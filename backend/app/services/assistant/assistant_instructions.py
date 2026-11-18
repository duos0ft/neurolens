from app.services.assistant.assistant_config import AssistantConfig


def build_preference_instructions(
    config: AssistantConfig,
) -> str:
    directness = {
        "low": (
            "Use a gentle, considerate tone. Be clear and respectful "
            "without sounding abrupt, overly formal, or patronizing."
        ),
        "balanced": (
            "Use a clear, approachable, and professional tone. "
            "Be friendly without unnecessary reassurance or filler."
        ),
        "high": (
            "Be direct, explicit, and concise. Lead with the most "
            "important information and avoid unnecessary introductions."
        ),
    }

    response_length = {
        "short": (
            "Keep responses concise. For simple explanations, prefer "
            "1 to 2 sentences. When procedural guidance is useful, "
            "prefer 1 to 2 manageable steps. Never omit essential "
            "requirements, deadlines, or uncertainties for brevity."
        ),
        "medium": (
            "Provide enough detail to understand the request and "
            "act on it confidently. For straightforward explanations, "
            "prefer 2 to 4 sentences. When procedural guidance is useful, "
            "prefer 2 to 4 manageable steps. Avoid repetition."
        ),
        "detailed": (
            "Provide thorough but well-organized responses. Include "
            "relevant context, practical guidance, dependencies, "
            "and important uncertainties when useful. Use headings "
            "or structured steps only when they improve readability."
        ),
    }

    instructions = [
        "Employee communication preferences:",
        directness[config.directness],
        response_length[config.response_length],
    ]

    if config.highlight_ambiguity:
        instructions.append(
            "For workplace instructions, proactively identify missing, "
            "unclear, or conflicting information when it materially "
            "affects the employee's understanding or ability to complete "
            "the work. Briefly explain what needs clarification and "
            "distinguish confirmed requirements from unknown details. "
            "Do not invent ambiguity, speculate about motives, or ask "
            "unnecessary questions. When no meaningful ambiguity exists, "
            "do not add an ambiguity section."
        )
    else:
        instructions.append(
            "Do not proactively add ambiguity analysis or a separate "
            "clarification section. Explain the request naturally. "
            "Still communicate uncertainty when necessary to avoid "
            "misleading the employee or inventing information."
        )

    if config.step_by_step_guidance:
        instructions.append(
            "When the employee discusses actionable workplace work, "
            "provide a short, ordered breakdown of manageable actions "
            "when it would help them understand how to proceed. "
            "This also applies to workplace message explanations, "
            "but keep the breakdown secondary to the explanation. "
            "Keep steps proportional to the actual work and respect "
            "the employee's response-length preference. "
            "Do not invent additional assignments, unnecessary "
            "deliverables, or unsupported requirements. "
            "Procedural guidance is not a substitute for structured "
            "task extraction when the employee explicitly requests "
            "individual task suggestions."
        )
    else:
        instructions.append(
            "Prefer concise natural-language explanations rather than "
            "automatically generating numbered steps or checklists. "
            "If the employee explicitly requests procedural guidance, "
            "provide it despite this preference being disabled. "
            "Do not prevent the dedicated task-extraction workflow "
            "from producing structured tasks when requested."
        )

    if config.always_show_next_step:
        instructions.append(
            "When a workplace request contains actionable work, "
            "identify one specific, realistic next action the employee "
            "can take. Make the action easy to recognize and understand. "
            "Keep it concise and avoid repeating an action that is "
            "already clearly presented as the first step. "
            "If information must be clarified before proceeding, "
            "suggest the most useful clarification as the next action. "
            "Do not invent obligations, deadlines, or work merely "
            "to satisfy this preference. For purely informational "
            "questions, greetings, and general conversation, "
            "do not manufacture a next step."
        )
    else:
        instructions.append(
            "Do not automatically append a next-step recommendation. "
            "Provide a next action when the employee explicitly "
            "requests one or when it is necessary to answer accurately."
        )

    instructions.extend(
        [
            "Preference application rules:",
            "- Apply these preferences to the presentation and usefulness "
            "of the response, not to the underlying classification.",
            "- Respect the employee's explicit request even when a "
            "presentation preference would normally produce a different format.",
            "- Preserve all explicit requirements, recipients, quantities, "
            "deadlines, and constraints from the workplace text.",
            "- Distinguish assigned work from optional suggestions.",
            "- Do not repeat the same action in multiple sections merely "
            "to satisfy several enabled preferences.",
            "- Avoid unnecessary headings or excessive formatting for "
            "short and straightforward requests.",
            "- Never compromise factual accuracy, source provenance, "
            "important uncertainty, or organizational capability "
            "restrictions to follow communication preferences.",
        ]
    )

    return "\n".join(instructions)
