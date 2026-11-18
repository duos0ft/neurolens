from app.ai.capabilities.message_explanation import StructuredExplanation
from app.ai.capabilities.text_generation import TextGenerationResponse
from app.ai.capabilities.types import AICapability
from app.services.assistant.assistant_config import AssistantConfig
from app.services.assistant.assistant_orchestrator import CapabilityResult

CAPABILITY_HEADINGS = {
    AICapability.GENERAL_CONVERSATION: "Response",
    AICapability.MESSAGE_EXPLANATION: "What this means",
    AICapability.TASK_ASSISTANCE: "What to do",
    AICapability.POLICY_QUESTION: "Company policy",
}


class AssistantResponseComposer:
    def _compose_explanation(
        self,
        explanation: StructuredExplanation,
        config: AssistantConfig,
    ) -> str:
        sections = [
            explanation.explanation,
        ]

        has_suggested_clarifications = config.highlight_ambiguity and bool(
            explanation.clarification_questions
        )

        if (
            config.highlight_ambiguity
            and explanation.ambiguities
            and not has_suggested_clarifications
        ):
            ambiguities = "\n".join(f"- {item}" for item in explanation.ambiguities)

            sections.append(f"**What needs clarification**\n\n{ambiguities}")

        if config.step_by_step_guidance and explanation.steps:
            steps = "\n".join(
                f"{index}. {step}"
                for index, step in enumerate(
                    explanation.steps,
                    start=1,
                )
            )

            sections.append(f"**How to approach it**\n\n{steps}")

        if (
            config.always_show_next_step
            and explanation.next_step
            and not (config.step_by_step_guidance and explanation.steps)
        ):
            sections.append(f"**Next step**\n\n{explanation.next_step}")

        return "\n\n".join(sections)

    def compose(
        self,
        results: list[CapabilityResult],
        config: AssistantConfig | None = None,
    ) -> TextGenerationResponse:
        if not results:
            return TextGenerationResponse(
                content=(
                    "Could you clarify what you'd like help with? "
                    "I can explain workplace messages or help you "
                    "break down tasks into manageable steps."
                ),
                model="neurolens",
            )

        resolved_config = config or AssistantConfig()

        sections: list[tuple[AICapability, str]] = []

        for result in results:
            if result.structured_explanation is not None:
                content = self._compose_explanation(
                    explanation=result.structured_explanation,
                    config=resolved_config,
                )
            else:
                content = result.response.content.strip()

            if content:
                sections.append((result.capability, content))

        if not sections:
            return TextGenerationResponse(
                content=("I couldn't generate a useful response. Could you rephrase your request?"),
                model="neurolens",
            )

        if len(results) == 1 and len(sections) == 1:
            _, content = sections[0]

            return TextGenerationResponse(
                content=content,
                model=results[0].response.model,
            )

        formatted_sections: list[str] = []

        for capability, content in sections:
            heading = CAPABILITY_HEADINGS.get(
                capability,
                "Additional information",
            )

            formatted_sections.append(f"### {heading}\n\n{content}")

        return TextGenerationResponse(
            content="\n\n".join(formatted_sections),
            model="neurolens-composed",
        )
