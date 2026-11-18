from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Auth0Identity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    provider: str
    user_id: str
    connection: str | None = None
    is_social: bool | None = None


class Auth0AppMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    neurolens_invitation_id: str | None = None


class Auth0User(BaseModel):
    model_config = ConfigDict(extra="ignore")

    user_id: str
    email: EmailStr
    email_verified: bool = False
    identities: list[Auth0Identity] = Field(default_factory=list)
    app_metadata: Auth0AppMetadata = Field(default_factory=Auth0AppMetadata)


class Auth0CreatePasswordlessUserRequest(BaseModel):
    connection: Literal["email"] = "email"
    email: EmailStr
    email_verified: bool = False
    app_metadata: Auth0AppMetadata


class Auth0AccessTokenResponse(BaseModel):
    access_token: str = Field(repr=False)
    token_type: str
    expires_in: int
