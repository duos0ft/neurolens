import math

from app.ai.capabilities.sentiment_analysis import (
    SentimentAnalysisError,
    SentimentPrediction,
    SentimentProvider,
)


class SentimentAnalysisService:
    def __init__(
        self,
        provider: SentimentProvider,
    ) -> None:
        self.provider = provider

    async def analyze(
        self,
        text: str,
    ) -> SentimentPrediction:
        normalized_text = text.strip()

        if not normalized_text:
            raise SentimentAnalysisError("Message cannot be empty")

        if len(normalized_text) > 10_000:
            raise SentimentAnalysisError("Message exceeds the maximum length")

        prediction = await self.provider.classify(normalized_text)

        if (
            prediction.label
            not in (
                "negative",
                "neutral",
                "positive",
            )
            or not math.isfinite(prediction.confidence)
            or not 0.0 <= prediction.confidence <= 1.0
        ):
            raise SentimentAnalysisError("Invalid sentiment prediction")

        return prediction
