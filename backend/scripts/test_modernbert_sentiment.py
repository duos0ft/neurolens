import asyncio
from time import perf_counter

from app.ai.providers.modernbert_sentiment import (
    ModernBERTSentimentProvider,
)

MESSAGES = [
    "Thank you for helping me resolve this issue!",
    "Please review the report before Friday.",
    "I'm frustrated that this problem still hasn't been resolved.",
    "I appreciate how quickly the team completed the project.",
    "We need to discuss the delays in the latest release.",
]


async def main() -> None:
    provider = ModernBERTSentimentProvider()

    for message in MESSAGES:
        started = perf_counter()

        prediction = await provider.classify(message)

        elapsed = perf_counter() - started

        print(f"\nMessage: {message}")
        print(f"Sentiment: {prediction.label}")
        print(f"Confidence: {prediction.confidence:.2%}")
        print(f"Time: {elapsed:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
