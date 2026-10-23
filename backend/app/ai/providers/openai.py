from openai import AsyncOpenAI

from app.ai.capabilities.text_generation import (
    TextGenerationRequest,
    TextGenerationResponse,
)


class OpenAITextGenerationProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
    ) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResponse:
        messages = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in request.messages
        ]

        if request.system_instructions:
            messages.insert(
                0,
                {
                    "role": "developer",
                    "content": request.system_instructions,
                },
            )

        response = await self.client.responses.create(
            model=self.model,
            input=messages,
        )

        return TextGenerationResponse(
            content=response.output_text,
            model=response.model,
        )
