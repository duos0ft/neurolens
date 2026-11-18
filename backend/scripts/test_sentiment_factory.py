import asyncio

from app.ai.providers.sentiment_factory import create_sentiment_provider


async def main() -> None:
    provider = create_sentiment_provider()

    prediction = await provider.classify("Thank you for helping me resolve this issue!")

    print(f"Provider: {type(provider).__name__}")
    print(f"Model: {prediction.model}")
    print(f"Sentiment: {prediction.label}")
    print(f"Confidence: {prediction.confidence:.2%}")


if __name__ == "__main__":
    asyncio.run(main())
