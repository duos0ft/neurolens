from dataclasses import dataclass

from app.ai.capabilities.types import AICapability
from app.services.assistant_execution_result import AssistantExecutionResult
from app.services.conversation_context_snapshot import (
    ConversationContextSnapshot,
)
from app.services.policy_answer import PolicyAnswerStatus, PolicyCitation

METADATA_VERSION = 3

SUPPORTED_CAPABILITIES = {
    AICapability.GENERAL_CONVERSATION,
    AICapability.MESSAGE_EXPLANATION,
    AICapability.TASK_ASSISTANCE,
    AICapability.TASK_EXTRACTION,
    AICapability.POLICY_QUESTION,
}


@dataclass(frozen=True)
class ConversationCapabilityMetadata:
    capabilities: tuple[AICapability, ...]
    sources: tuple[ConversationContextSnapshot, ...] = ()
    policy_status: PolicyAnswerStatus | None = None
    citations: tuple[PolicyCitation, ...] = ()

    def __post_init__(self) -> None:
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError("Duplicate capabilities are not allowed")

        if any(capability not in SUPPORTED_CAPABILITIES for capability in self.capabilities):
            raise ValueError("Unsupported execution capability")

        source_capabilities = [source.capability for source in self.sources]

        if len(set(source_capabilities)) != len(source_capabilities):
            raise ValueError("Duplicate source capabilities")

        if any(capability not in self.capabilities for capability in source_capabilities):
            raise ValueError("Source capability must belong to the execution result")

        # Policy answers must never carry reusable conversation source data.
        # A mixed request may still store the specialist's quoted source; the
        # follow-up context resolver never reuses mixed-capability exchanges.
        if AICapability.POLICY_QUESTION in source_capabilities:
            raise ValueError("Policy-related responses cannot contain source snapshots")

        has_policy = AICapability.POLICY_QUESTION in self.capabilities

        if (self.policy_status is not None or self.citations) and not has_policy:
            raise ValueError("Policy metadata requires a policy capability")

        if self.citations and self.policy_status != PolicyAnswerStatus.ANSWERED:
            raise ValueError("Only answered policy questions can carry citations")

        if self.policy_status == PolicyAnswerStatus.ANSWERED and not self.citations:
            raise ValueError("Answered policy questions must carry citations")

        numbers = [citation.number for citation in self.citations]

        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError("Citation numbers must be sequential")

    @classmethod
    def from_execution_result(
        cls,
        result: AssistantExecutionResult,
    ) -> "ConversationCapabilityMetadata":
        return cls(
            capabilities=result.capabilities,
            sources=result.sources,
            policy_status=result.policy_status,
            citations=result.citations,
        )

    def to_dict(self) -> dict:
        return {
            "version": METADATA_VERSION,
            "capabilities": [capability.value for capability in self.capabilities],
            "sources": [source.to_dict() for source in self.sources],
            "policy": (
                {
                    "status": self.policy_status.value,
                    "citations": [citation.to_dict() for citation in self.citations],
                }
                if self.policy_status is not None
                else None
            ),
        }

    @classmethod
    def from_dict(
        cls,
        value: dict,
    ) -> "ConversationCapabilityMetadata":
        if not isinstance(value, dict):
            raise ValueError("Invalid capability metadata")

        version = value.get("version")

        if type(version) is not int or version not in (1, 2, 3):
            raise ValueError("Unsupported capability metadata version")

        raw_capabilities = value.get("capabilities")

        if not isinstance(raw_capabilities, list):
            raise ValueError("Invalid capability metadata")

        try:
            capabilities = tuple(AICapability(capability) for capability in raw_capabilities)

        except (ValueError, TypeError) as error:
            raise ValueError("Invalid execution capability") from error

        if version == 1:
            return cls(
                capabilities=capabilities,
            )

        raw_sources = value.get("sources")

        if not isinstance(raw_sources, list):
            raise ValueError("Invalid source metadata")

        try:
            sources = tuple(ConversationContextSnapshot.from_dict(source) for source in raw_sources)

        except (ValueError, TypeError, KeyError) as error:
            raise ValueError("Invalid source metadata") from error

        policy_status = None
        citations: tuple[PolicyCitation, ...] = ()

        raw_policy = value.get("policy") if version >= 3 else None

        if raw_policy is not None:
            if not isinstance(raw_policy, dict):
                raise ValueError("Invalid policy metadata")

            raw_citations = raw_policy.get("citations", [])

            if not isinstance(raw_citations, list):
                raise ValueError("Invalid policy metadata")

            try:
                policy_status = PolicyAnswerStatus(raw_policy.get("status"))
                citations = tuple(PolicyCitation.from_dict(item) for item in raw_citations)

            except (ValueError, TypeError) as error:
                raise ValueError("Invalid policy metadata") from error

        return cls(
            capabilities=capabilities,
            sources=sources,
            policy_status=policy_status,
            citations=citations,
        )
