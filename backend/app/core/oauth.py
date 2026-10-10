from authlib.integrations.httpx_client import AsyncOAuth2Client

from app.core.settings import settings

AUTH0_BASE_URL = f"https://{settings.auth0_domain}"


def create_auth0_client() -> AsyncOAuth2Client:
    return AsyncOAuth2Client(
        client_id=settings.auth0_client_id,
        client_secret=settings.auth0_client_secret,
        redirect_uri=settings.auth0_redirect_uri,
        scope="openid profile email",
        code_challenge_method="S256",
    )


def get_auth0_token_url() -> str:
    return f"{AUTH0_BASE_URL}/oauth/token"


def get_auth0_jwks_url() -> str:
    return f"{AUTH0_BASE_URL}/.well-known/jwks.json"


def get_auth0_issuer() -> str:
    return f"{AUTH0_BASE_URL}/"
