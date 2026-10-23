from openai import APIError, APITimeoutError, AsyncOpenAI

from app.ai.capabilities.text_generation import (
    TextGenerationError,
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

        try:
            response = await self.client.responses.create(
                model=self.model,
                instructions=request.system_instructions,
                input=messages,
            )

        except (APIError, APITimeoutError) as error:
            raise TextGenerationError("Text generation provider unavailable") from error

        if not response.output_text:
            raise TextGenerationError("Text generation provider returned an empty response")

        return TextGenerationResponse(
            content=response.output_text,
            model=response.model,
        )
