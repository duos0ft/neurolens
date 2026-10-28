from app.ai.capabilities.text_generation import TextGenerationResponse
from app.ai.capabilities.types import AICapability
from app.services.assistant_orchestrator import CapabilityResult

CAPABILITY_HEADINGS = {
    AICapability.GENERAL_CONVERSATION: "Response",
    AICapability.MESSAGE_EXPLANATION: "What this means",
    AICapability.TASK_ASSISTANCE: "What to do",
    AICapability.POLICY_QUESTION: "Company policy",
}


class AssistantResponseComposer:
    def compose(
        self,
        results: list[CapabilityResult],
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

        if len(results) == 1:
            return results[0].response

        sections: list[str] = []

        for result in results:
            content = result.response.content.strip()

            if not content:
                continue

            heading = CAPABILITY_HEADINGS.get(
                result.capability,
                "Additional information",
            )

            sections.append(f"### {heading}\n\n{content}")

        if not sections:
            return TextGenerationResponse(
                content=("I couldn't generate a useful response. Could you rephrase your request?"),
                model="neurolens",
            )

        return TextGenerationResponse(
            content="\n\n".join(sections),
            model="neurolens-composed",
        )
