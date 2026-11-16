from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.capabilities.embeddings import EmbeddingProvider
from app.services.policy_context import (
    PolicyCitation,
    PolicyContextService,
)
from app.services.policy_retrieval import PolicyRetrievalService


@dataclass(frozen=True)
class PreparedPolicyQuestion:
    question: str
    context: str
    citations: list[PolicyCitation]
    has_evidence: bool


class PolicyQuestionService:
    def __init__(
        self,
        db: AsyncSession,
        embedding_provider: EmbeddingProvider,
    ):
        self.retrieval = PolicyRetrievalService(
            db=db,
            embedding_provider=embedding_provider,
        )
        self.context_service = PolicyContextService()

    async def prepare(
        self,
        question: str,
        limit: int = 5,
    ) -> PreparedPolicyQuestion:
        normalized_question = question.strip()

        if not normalized_question:
            raise ValueError("Policy question cannot be empty")

        results = await self.retrieval.search(
            query=normalized_question,
            limit=limit,
        )

        context = self.context_service.build(results)

        return PreparedPolicyQuestion(
            question=normalized_question,
            context=context.text,
            citations=context.citations,
            has_evidence=bool(context.citations),
        )
