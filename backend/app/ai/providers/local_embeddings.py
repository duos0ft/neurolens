import hashlib
import math
import re

from app.ai.capabilities.embeddings import EmbeddingPurpose, EmbeddingResult

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "if",
        "in",
        "is",
        "it",
        "its",
        "may",
        "me",
        "my",
        "of",
        "on",
        "or",
        "our",
        "should",
        "that",
        "the",
        "their",
        "this",
        "to",
        "we",
        "what",
        "when",
        "which",
        "who",
        "will",
        "with",
        "you",
        "your",
    }
)

SUFFIXES = ("ing", "ies", "ed", "es", "s")


def _stem(token: str) -> str:
    for suffix in SUFFIXES:
        if len(token) > len(suffix) + 2 and token.endswith(suffix):
            return token[: -len(suffix)]

    return token


def _features(text: str) -> list[str]:
    tokens = [
        _stem(token) for token in TOKEN_PATTERN.findall(text.lower()) if token not in STOP_WORDS
    ]

    bigrams = [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]

    return tokens + bigrams


class HashingEmbeddingProvider:
    """Deterministic, offline embedding provider based on feature hashing.

    It needs no network access or API key, which makes it suitable for tests,
    CI and local development. Retrieval quality is lexical rather than
    semantic, so production deployments should use a model-based provider.
    """

    def __init__(self, dimensions: int = 512) -> None:
        if dimensions < 16:
            raise ValueError("Embedding dimensions must be at least 16")

        self.dimensions = dimensions

    @property
    def model_id(self) -> str:
        return f"local:hashing-v1-{self.dimensions}"

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions

        for feature in _features(text):
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % self.dimensions
            sign = 1.0 if (value >> 63) & 1 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(component * component for component in vector))

        if norm == 0:
            return vector

        return [component / norm for component in vector]

    async def embed(
        self,
        texts: list[str],
        purpose: EmbeddingPurpose,
    ) -> EmbeddingResult:
        del purpose

        return EmbeddingResult(
            vectors=[self._embed_one(text) for text in texts],
            model=self.model_id,
        )
