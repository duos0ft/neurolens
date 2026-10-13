from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ResendSendEmailRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sender: EmailStr = Field(alias="from")
    to: list[EmailStr] = Field(min_length=1)
    subject: str = Field(min_length=1)
    html: str = Field(min_length=1)


class ResendSendEmailResponse(BaseModel):
    id: str = Field(min_length=1)
