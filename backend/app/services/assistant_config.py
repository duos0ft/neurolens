from dataclasses import dataclass


@dataclass(frozen=True)
class AssistantConfig:
    enable_task_assistance: bool = True
    enable_policy_assistance: bool = False
    enable_sentiment_analysis: bool = False

    directness: str = "balanced"
    response_length: str = "medium"
    highlight_ambiguity: bool = True
    step_by_step_guidance: bool = True
    always_show_next_step: bool = False