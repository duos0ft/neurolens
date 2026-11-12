from pydantic import BaseModel, ConfigDict, Field, field_validator


class StructuredExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    explanation: str = Field(min_length=1)
    ambiguities: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    next_step: str | None = None

    @field_validator("explanation")
    @classmethod
    def validate_explanation(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Explanation cannot be empty")

        return value

    @field_validator("ambiguities", "clarification_questions", "steps")
    @classmethod
    def validate_items(cls, values: list[str]) -> list[str]:
        validated: list[str] = []

        for value in values:
            value = value.strip()

            if not value:
                raise ValueError("Items cannot be empty")

            validated.append(value)

        return validated

    @field_validator("next_step")
    @classmethod
    def validate_next_step(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None
