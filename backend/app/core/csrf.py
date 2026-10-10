from urllib.parse import urlsplit

from fastapi import HTTPException, Request, status

from app.core.settings import settings


def validate_request_origin(request: Request) -> None:
    origin = request.headers.get("origin")

    expected = urlsplit(settings.frontend_url)

    if not origin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing Origin header",
        )

    received = urlsplit(origin)

    if (
        received.scheme != expected.scheme
        or received.netloc != expected.netloc
        or received.username is not None
        or received.password is not None
        or received.path not in ("", "/")
        or received.query
        or received.fragment
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid request origin",
        )
