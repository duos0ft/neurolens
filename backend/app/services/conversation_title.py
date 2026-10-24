import asyncio

from app.ai.capabilities.text_generation import (
    GenerationMessage,
    TextGenerationProvider,
    TextGenerationRequest,
)

TITLE_MAX_LENGTH = 60
TITLE_GENERATION_TIMEOUT = 5

TITLE_INSTRUCTIONS = """
Generate a short, descriptive title for a workplace assistant conversation.

Rules:
- Describe the topic, not the employee.
- Prefer 3 to 7 words.
- Use the same language as the user.
- Use a neutral, professional tone.
- Do not include personal names, email addresses, diagnoses,
  medical information, or other sensitive personal details.
- Do not invent company policies or procedures.
- Return only the title.
- Do not include quotation marks, Markdown, or explanations.
- Maximum 60 characters.
"""


class ConversationTitleService:
    def __init__(
        self,
        provider: TextGenerationProvider,
    ) -> None:
        self.provider = provider

    async def generate(
        self,
        user_message: str,
        assistant_response: str,
    ) -> str:
        request = TextGenerationRequest(
            system_instructions=TITLE_INSTRUCTIONS,
            messages=[
                GenerationMessage(
                    role="user",
                    content=(
                        "Create a title for the following conversation.\n\n"
                        f"User message:\n{user_message[:2000]}\n\n"
                        f"Assistant response:\n{assistant_response[:2000]}"
                    ),
                ),
            ],
        )

        async with asyncio.timeout(TITLE_GENERATION_TIMEOUT):
            response = await self.provider.generate(request)

        title = " ".join(response.content.split())
        title = title.strip(" \"'`*_#")

        if len(title) > TITLE_MAX_LENGTH:
            title = title[:TITLE_MAX_LENGTH].rstrip()

        return title