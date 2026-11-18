from functools import lru_cache

from app.ai.capabilities.sentiment_analysis import SentimentProvider
from app.ai.providers.modernbert_sentiment import ModernBERTSentimentProvider
from app.core.settings import settings


@lru_cache(maxsize=1)
def create_sentiment_provider() -> SentimentProvider:
    if settings.ai_sentiment_provider == "modernbert":
        return ModernBERTSentimentProvider()

    raise ValueError(f"Unsupported sentiment provider: {settings.ai_sentiment_provider}")
