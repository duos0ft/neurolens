from enum import StrEnum

from pydantic import BaseModel


class Auth0ErrorCategory(StrEnum):
    PERMANENT = "permanent"
    TRANSIENT = "transient"
    UNCERTAIN = "uncertain"


class Auth0Operation(StrEnum):
    TOKEN = "token"
    LOOKUP_USER = "lookup_user"
    CREATE_USER = "create_user"


class Auth0ErrorResult(BaseModel):
    operation: Auth0Operation
    category: Auth0ErrorCategory
    status_code: int | None = None
    error_code: str
