from pydantic import BaseModel, Field

from app.schemas.conversation import PolicyCitationResponse


class AssistantMessageRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=10000,
    )


class AssistantMessageResponse(BaseModel):
    content: str
    model: str
    citations: list[PolicyCitationResponse] = Field(default_factory=list)
