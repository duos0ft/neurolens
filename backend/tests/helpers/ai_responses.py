import json

from app.ai.capabilities.text_generation import TextGenerationResponse


def explanation_response(
    explanation: str,
    *,
    ambiguities: list[str] | None = None,
    steps: list[str] | None = None,
    next_step: str | None = None,
    model: str = "test-model",
) -> TextGenerationResponse:
    return TextGenerationResponse(
        content=json.dumps(
            {
                "explanation": explanation,
                "ambiguities": ambiguities or [],
                "steps": steps or [],
                "next_step": next_step,
            }
        ),
        model=model,
    )
