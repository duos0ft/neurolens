from dataclasses import dataclass
from typing import Literal

Directness = Literal["low", "balanced", "high"]
ResponseLength = Literal["short", "medium", "detailed"]


@dataclass(frozen=True)
class AssistantConfig:
    enable_task_assistance: bool = True
    enable_policy_assistance: bool = False
    enable_sentiment_analysis: bool = False

    directness: Directness = "balanced"
    response_length: ResponseLength = "medium"
    highlight_ambiguity: bool = True
    step_by_step_guidance: bool = True
    always_show_next_step: bool = True
