import uuid
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.calendar_integration import CalendarIntegration
from app.services.calendar.calendar_token_encryption import (
    CalendarTokenEncryption,
    CalendarTokenEncryptionError,
)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class GoogleCalendarTokenError(Exception):
    pass


class GoogleCalendarReconnectRequiredError(GoogleCalendarTokenError):
    pass


@dataclass(frozen=True)
class GoogleCalendarAccessToken:
    token: str
    expires_in: int


class GoogleCalendarTokenService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_access_token(
        self,
        employee_id: uuid.UUID,
    ) -> GoogleCalendarAccessToken:
        if not settings.google_calendar_client_id or not settings.google_calendar_client_secret:
            raise GoogleCalendarTokenError("Google Calendar OAuth is not configured")

        connection = await self.db.scalar(
            select(CalendarIntegration).where(
                CalendarIntegration.employee_id == employee_id,
                CalendarIntegration.provider == "google",
            )
        )

        if connection is None:
            raise GoogleCalendarReconnectRequiredError("Google Calendar is not connected")

        try:
            refresh_token = CalendarTokenEncryption().decrypt(connection.encrypted_refresh_token)
        except CalendarTokenEncryptionError as error:
            raise GoogleCalendarTokenError(
                "Unable to access Google Calendar credentials"
            ) from error

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        "client_id": settings.google_calendar_client_id,
                        "client_secret": settings.google_calendar_client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
        except httpx.HTTPError as error:
            raise GoogleCalendarTokenError(
                "Google Calendar token refresh request failed"
            ) from error

        if response.status_code != 200:
            if response.status_code == 400:
                try:
                    error_data = response.json()
                except ValueError:
                    error_data = {}

                if isinstance(error_data, dict) and error_data.get("error") == "invalid_grant":
                    raise GoogleCalendarReconnectRequiredError(
                        "Google Calendar authorization has expired or been revoked"
                    )

            raise GoogleCalendarTokenError("Google Calendar token refresh was unsuccessful")

        try:
            data = response.json()
        except ValueError as error:
            raise GoogleCalendarTokenError("Invalid Google Calendar token response") from error

        if not isinstance(data, dict):
            raise GoogleCalendarTokenError("Invalid Google Calendar token response")

        access_token = data.get("access_token")
        expires_in = data.get("expires_in")

        if (
            not isinstance(access_token, str)
            or not access_token
            or type(expires_in) is not int
            or expires_in <= 0
        ):
            raise GoogleCalendarTokenError("Google Calendar returned invalid access token data")

        return GoogleCalendarAccessToken(
            token=access_token,
            expires_in=expires_in,
        )
