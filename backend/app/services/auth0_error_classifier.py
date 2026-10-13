import httpx

from app.schemas.auth0_errors import (
    Auth0ErrorCategory,
    Auth0ErrorResult,
    Auth0Operation,
)


def classify_auth0_error(
    error: httpx.HTTPError,
    operation: Auth0Operation,
) -> Auth0ErrorResult:
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code

        if operation == Auth0Operation.CREATE_USER:
            if status >= 500 or status in (408, 409, 429):
                category = Auth0ErrorCategory.UNCERTAIN
            elif 400 <= status < 500:
                category = Auth0ErrorCategory.PERMANENT
            else:
                category = Auth0ErrorCategory.UNCERTAIN
        elif status == 429 or status >= 500:
            category = Auth0ErrorCategory.TRANSIENT
        elif 400 <= status < 500:
            category = Auth0ErrorCategory.PERMANENT
        else:
            category = Auth0ErrorCategory.UNCERTAIN

        return Auth0ErrorResult(
            operation=operation,
            category=category,
            status_code=status,
            error_code=f"auth0_http_{status}",
        )

    if operation == Auth0Operation.CREATE_USER:
        category = Auth0ErrorCategory.UNCERTAIN
    else:
        category = Auth0ErrorCategory.TRANSIENT

    return Auth0ErrorResult(
        operation=operation,
        category=category,
        error_code="auth0_transport_error",
    )


class Auth0OperationError(Exception):
    def __init__(self, result: Auth0ErrorResult) -> None:
        self.result = result
        super().__init__(f"Auth0 {result.operation.value} failed: {result.error_code}")
