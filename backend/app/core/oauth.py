from authlib.integrations.httpx_client import AsyncOAuth2Client

from app.core.settings import settings


def create_auth0_client() -> AsyncOAuth2Client:
    return AsyncOAuth2Client(
        client_id=settings.auth0_client_id,
        client_secret=settings.auth0_client_secret,
        redirect_uri=settings.auth0_redirect_uri,
        scope="openid profile email",
        code_challenge_method="S256",
    )