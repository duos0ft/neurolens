import asyncio
from functools import lru_cache
from typing import Any

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from app.ai.capabilities.sentiment_analysis import (
    SentimentAnalysisError,
    SentimentPrediction,
)

MODEL_ID = "aieng-lab/ModernBERT-base_sentiment"
MAX_LENGTH = 128

LABEL_MAPPING = {
    0: "negative",
    1: "neutral",
    2: "positive",
}


@lru_cache(maxsize=1)
def load_model() -> tuple[Any, Any]:
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_ID,
        attn_implementation="sdpa",
    )

    if model.config.num_labels != len(LABEL_MAPPING):
        raise SentimentAnalysisError("Unexpected number of sentiment classes")

    expected_labels = {index: f"LABEL_{index}" for index in LABEL_MAPPING}

    actual_labels = {int(index): label for index, label in model.config.id2label.items()}

    if actual_labels != expected_labels:
        raise SentimentAnalysisError(f"Unexpected model label configuration: {actual_labels}")

    model.eval()

    return tokenizer, model


class ModernBERTSentimentProvider:
    def __init__(self) -> None:
        self.semaphore = asyncio.Semaphore(1)

    def _classify_sync(
        self,
        text: str,
    ) -> SentimentPrediction:
        tokenizer, model = load_model()

        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_LENGTH,
        )

        with torch.inference_mode():
            logits = model(**inputs).logits
            probabilities = torch.softmax(
                logits,
                dim=-1,
            )[0]

        index = int(probabilities.argmax().item())

        label = LABEL_MAPPING[index]

        confidence = float(probabilities[index].item())

        return SentimentPrediction(
            label=label,
            confidence=confidence,
            model=MODEL_ID,
        )

    async def classify(
        self,
        text: str,
    ) -> SentimentPrediction:
        normalized_text = text.strip()

        if not normalized_text:
            raise SentimentAnalysisError("Text cannot be empty")

        if len(normalized_text) > 10_000:
            raise SentimentAnalysisError("Text exceeds the maximum length")

        async with self.semaphore:
            try:
                return await asyncio.to_thread(
                    self._classify_sync,
                    normalized_text,
                )
            except SentimentAnalysisError:
                raise
            except Exception as error:
                raise SentimentAnalysisError("Unable to analyze sentiment") from error
