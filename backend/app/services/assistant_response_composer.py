from app.ai.capabilities.text_generation import TextGenerationResponse
from app.ai.capabilities.types import AICapability
from app.services.assistant_orchestrator import CapabilityResult


class AssistantResponseComposer:
    def compose(
        self,
        results: list[CapabilityResult],
    ) -> TextGenerationResponse:
        if not results:
            return TextGenerationResponse(
                content=(
                    "Could you clarify what you'd like help with? "
                    "I can explain workplace messages or help organize "
                    "tasks when that capability is available."
                ),
                model="neurolens",
            )

        if len(results) == 1:
            return results[0].response

        headings = {
            AICapability.GENERAL_CONVERSATION: "Response",
            AICapability.MESSAGE_EXPLANATION: "Message explanation",
            AICapability.TASK_ASSISTANCE: "Suggested steps",
            AICapability.POLICY_QUESTION: "Company policy",
        }

        sections: list[str] = []

        for result in results:
            sections.append(
                f"**{headings[result.capability]}**\n\n{result.response.content.strip()}"
            )

        return TextGenerationResponse(
            content="\n\n".join(sections),
            model="neurolens-composed",
        )