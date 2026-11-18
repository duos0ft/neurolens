from dataclasses import dataclass
from typing import Literal, Protocol

SentimentLabel = Literal[
    "negative",
    "neutral",
    "positive",
]


@dataclass(frozen=True)
class SentimentPrediction:
    label: SentimentLabel
    confidence: float
    model: str


class SentimentProvider(Protocol):
    async def classify(
        self,
        text: str,
    ) -> SentimentPrediction: ...


class SentimentAnalysisError(Exception):
    pass
