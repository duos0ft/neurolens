import secrets
import time

import httpx
from joserfc import jwt
from joserfc.jwk import KeySet
from joserfc.jwt import JWTClaimsRegistry

from app.core.oauth import get_auth0_issuer, get_auth0_jwks_url
from app.core.settings import settings


async def verify_id_token(
    id_token: str,
    expected_nonce: str,
) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(get_auth0_jwks_url())
        response.raise_for_status()

    key_set = KeySet.import_key_set(response.json())

    token = jwt.decode(
        id_token,
        key_set,
        algorithms=["RS256"],
    )

    claims = token.claims

    registry = JWTClaimsRegistry(
        iss={
            "essential": True,
            "value": get_auth0_issuer(),
        },
        aud={
            "essential": True,
            "value": settings.auth0_client_id,
        },
        sub={"essential": True},
        exp={"essential": True},
        iat={"essential": True},
        nonce={"essential": True},
    )

    registry.validate(claims)

    now = int(time.time())

    if claims["exp"] <= now:
        raise ValueError("ID token has expired")

    if claims["iat"] > now + 60:
        raise ValueError("Invalid ID token issued-at time")

    if not isinstance(claims["sub"], str) or not claims["sub"]:
        raise ValueError("Invalid subject")

    if not secrets.compare_digest(
        str(claims["nonce"]),
        expected_nonce,
    ):
        raise ValueError("Invalid OIDC nonce")

    audience = claims["aud"]

    if isinstance(audience, list) and len(audience) > 1:
        if claims.get("azp") != settings.auth0_client_id:
            raise ValueError("Invalid authorized party")

    return dict(claims)
