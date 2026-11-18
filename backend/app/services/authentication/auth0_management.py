import uuid
from typing import Any

import httpx

from app.core.settings import settings
from app.schemas.authentication.auth0 import (
    Auth0AccessTokenResponse,
    Auth0AppMetadata,
    Auth0CreatePasswordlessUserRequest,
    Auth0User,
)
from app.schemas.authentication.auth0_errors import Auth0Operation
from app.services.authentication.auth0_error_classifier import (
    Auth0OperationError,
    classify_auth0_error,
)


class Auth0IdentityConflictError(Exception):
    pass


class Auth0ManagementService:
    def __init__(self) -> None:
        self.base_url = f"https://{settings.auth0_domain}"
        self.client_id = settings.auth0_management_client_id
        self.client_secret = settings.auth0_management_client_secret

    @staticmethod
    async def _request(
        client: httpx.AsyncClient,
        method: str,
        url: str,
        operation: Auth0Operation,
        **kwargs: Any,
    ) -> httpx.Response:
        try:
            response = await client.request(
                method,
                url,
                **kwargs,
            )
            response.raise_for_status()
            return response

        except httpx.HTTPError as error:
            result = classify_auth0_error(
                error=error,
                operation=operation,
            )
            raise Auth0OperationError(result) from error

    async def get_access_token(self) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await self._request(
                client,
                "POST",
                f"{self.base_url}/oauth/token",
                Auth0Operation.TOKEN,
                json={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "audience": f"{self.base_url}/api/v2/",
                },
            )

        token = Auth0AccessTokenResponse.model_validate(response.json())

        return token.access_token

    async def create_passwordless_user(
        self,
        email: str,
        invitation_id: uuid.UUID,
        access_token: str,
    ) -> Auth0User:
        request = Auth0CreatePasswordlessUserRequest(
            email=email,
            app_metadata=Auth0AppMetadata(
                neurolens_invitation_id=str(invitation_id),
            ),
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await self._request(
                client,
                "POST",
                f"{self.base_url}/api/v2/users",
                Auth0Operation.CREATE_USER,
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
                json=request.model_dump(mode="json"),
            )

        return Auth0User.model_validate(response.json())

    async def get_passwordless_user(
        self,
        email: str,
    ) -> Auth0User | None:
        access_token = await self.get_access_token()

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await self._request(
                client,
                "GET",
                f"{self.base_url}/api/v2/users-by-email",
                Auth0Operation.LOOKUP_USER,
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
                params={"email": email},
            )

        users = [Auth0User.model_validate(user) for user in response.json()]

        passwordless_users = [
            user
            for user in users
            if any(
                identity.provider == "email" and identity.connection == "email"
                for identity in user.identities
            )
        ]

        if len(passwordless_users) > 1:
            raise Auth0IdentityConflictError(
                "Multiple Auth0 passwordless identities found for the same email"
            )

        return passwordless_users[0] if passwordless_users else None

    async def reconcile_invitation(
        self,
        email: str,
        invitation_id: uuid.UUID,
    ) -> Auth0User | None:
        user = await self.get_passwordless_user(email)

        if user is None:
            return None

        if user.app_metadata.neurolens_invitation_id != str(invitation_id):
            raise Auth0IdentityConflictError(
                "Auth0 identity is not linked to this NeuroLens invitation"
            )

        return user
