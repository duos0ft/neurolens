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
                    "I couldn't determine which type of assistance "
                    "you need. Could you clarify whether you'd like "
                    "a message explained or help organizing a task?"
                ),
                model="neurolens",
            )

        if len(results) == 1:
            return results[0].response

        sections: list[str] = []

        headings = {
            AICapability.MESSAGE_EXPLANATION: "Message explanation",
            AICapability.TASK_ASSISTANCE: "Suggested steps",
        }

        for result in results:
            heading = headings[result.capability]

            sections.append(f"**{heading}**\n\n{result.response.content.strip()}")

        return TextGenerationResponse(
            content="\n\n".join(sections),
            model="neurolens-composed",
        )