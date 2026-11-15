import hashlib
from urllib.parse import quote

import httpx

from app.integrations.calendar.provider import (
    ExternalCalendarEvent,
    ExternalEventDraft,
    ExternalEventStatus,
)


GOOGLE_CALENDAR_API_URL = "https://www.googleapis.com/calendar/v3"


class GoogleCalendarEventError(Exception):
    pass


class GoogleCalendarAuthorizationError(GoogleCalendarEventError):
    pass


class GoogleCalendarRetryableError(GoogleCalendarEventError):
    pass


class GoogleCalendarEventNotFoundError(GoogleCalendarEventError):
    pass


class GoogleCalendarEventService:
    def __init__(self, access_token: str) -> None:
        self.access_token = access_token

    @staticmethod
    def _event_id(idempotency_key: str) -> str:
        if not idempotency_key:
            raise ValueError("Idempotency key is required")

        digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()

        return f"nl{digest}"

    @staticmethod
    def _serialize_time(value) -> dict:
        if value.date is not None:
            return {
                "date": value.date.isoformat(),
            }

        result = {
            "dateTime": value.datetime.isoformat(),
        }

        if value.timezone is not None:
            result["timeZone"] = value.timezone

        return result

    @classmethod
    def _create_payload(
        cls,
        event: ExternalEventDraft,
        event_id: str,
    ) -> dict:
        payload = {
            "id": event_id,
            "summary": event.title,
            "start": cls._serialize_time(event.start),
            "end": cls._serialize_time(event.end),
            "extendedProperties": {
                "private": {
                    "neurolens_idempotency_key_hash": event_id,
                },
            },
        }

        if event.description is not None:
            payload["description"] = event.description

        if event.location is not None:
            payload["location"] = event.location

        return payload

    @staticmethod
    def _to_external_event(
        data: dict,
        calendar_id: str,
        draft: ExternalEventDraft,
    ) -> ExternalCalendarEvent:
        event_id = data.get("id")

        if not isinstance(event_id, str) or not event_id:
            raise GoogleCalendarEventError("Google returned an event without an identifier")

        status_value = data.get("status", "confirmed")

        try:
            event_status = ExternalEventStatus(status_value)
        except ValueError as error:
            raise GoogleCalendarEventError("Google returned an unsupported event status") from error

        return ExternalCalendarEvent(
            id=event_id,
            calendar_id=calendar_id,
            title=data.get("summary", draft.title),
            start=draft.start,
            end=draft.end,
            status=event_status,
            description=data.get("description", draft.description),
            location=data.get("location", draft.location),
            provider_etag=data.get("etag"),
            provider_ical_uid=data.get("iCalUID"),
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    @staticmethod
    def _check_response(response: httpx.Response) -> None:
        if response.status_code in (401, 403):
            raise GoogleCalendarAuthorizationError("Google Calendar access was denied")

        if response.status_code == 429 or response.status_code >= 500:
            raise GoogleCalendarRetryableError("Google Calendar is temporarily unavailable")

        if response.status_code >= 400:
            raise GoogleCalendarEventError("Google Calendar rejected the event request")

    async def create_event(
        self,
        calendar_id: str,
        event: ExternalEventDraft,
        idempotency_key: str,
    ) -> ExternalCalendarEvent:
        event_id = self._event_id(idempotency_key)
        encoded_calendar_id = quote(calendar_id, safe="")

        collection_url = f"{GOOGLE_CALENDAR_API_URL}/calendars/{encoded_calendar_id}/events"

        payload = self._create_payload(event, event_id)

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    collection_url,
                    headers=self._headers(),
                    json=payload,
                    params={
                        "sendUpdates": "none",
                    },
                )

                if response.status_code == 409:
                    existing_response = await client.get(
                        f"{collection_url}/{quote(event_id, safe='')}",
                        headers=self._headers(),
                    )

                    self._check_response(existing_response)

                    data = existing_response.json()

                    if not isinstance(data, dict):
                        raise GoogleCalendarEventError("Invalid existing Google event")

                    properties = data.get(
                        "extendedProperties",
                        {},
                    )

                    if not isinstance(properties, dict):
                        raise GoogleCalendarEventError("Invalid existing event metadata")

                    private_properties = properties.get(
                        "private",
                        {},
                    )

                    if not isinstance(private_properties, dict):
                        raise GoogleCalendarEventError("Invalid existing event metadata")

                    if private_properties.get("neurolens_idempotency_key_hash") != event_id:
                        raise GoogleCalendarEventError("Google event identifier conflict")

                    return self._to_external_event(
                        data=data,
                        calendar_id=calendar_id,
                        draft=event,
                    )

                self._check_response(response)

                data = response.json()

                if not isinstance(data, dict):
                    raise GoogleCalendarEventError("Invalid Google event response")

                return self._to_external_event(
                    data=data,
                    calendar_id=calendar_id,
                    draft=event,
                )

        except httpx.TimeoutException as error:
            raise GoogleCalendarRetryableError("Google Calendar request timed out") from error

        except httpx.TransportError as error:
            raise GoogleCalendarRetryableError("Unable to reach Google Calendar") from error

        except ValueError as error:
            raise GoogleCalendarEventError("Invalid Google Calendar response") from error

    @staticmethod
    def _event_url(
        calendar_id: str,
        event_id: str,
    ) -> str:
        return (
            f"{GOOGLE_CALENDAR_API_URL}/calendars/"
            f"{quote(calendar_id, safe='')}/events/"
            f"{quote(event_id, safe='')}"
        )

    @classmethod
    def _verify_event_ownership(
        cls,
        data: dict,
        idempotency_key: str,
    ) -> None:
        expected_id = cls._event_id(idempotency_key)

        if data.get("id") != expected_id:
            raise GoogleCalendarEventError("Google event identifier does not match NeuroLens")

        properties = data.get("extendedProperties")

        if not isinstance(properties, dict):
            raise GoogleCalendarEventError("Google event ownership could not be verified")

        private_properties = properties.get("private")

        if not isinstance(private_properties, dict):
            raise GoogleCalendarEventError("Google event ownership could not be verified")

        if private_properties.get("neurolens_idempotency_key_hash") != expected_id:
            raise GoogleCalendarEventError(
                "Google event is not owned by this NeuroLens sync record"
            )

    async def _get_existing_event(
        self,
        client: httpx.AsyncClient,
        calendar_id: str,
        event_id: str,
        idempotency_key: str,
    ) -> dict:
        response = await client.get(
            self._event_url(calendar_id, event_id),
            headers=self._headers(),
        )

        if response.status_code in (404, 410):
            raise GoogleCalendarEventNotFoundError("Google event no longer exists")

        self._check_response(response)

        try:
            data = response.json()
        except ValueError as error:
            raise GoogleCalendarEventError("Invalid Google event response") from error

        if not isinstance(data, dict):
            raise GoogleCalendarEventError("Invalid Google event response")

        self._verify_event_ownership(
            data,
            idempotency_key,
        )

        return data

    async def update_event(
        self,
        calendar_id: str,
        event_id: str,
        event: ExternalEventDraft,
        idempotency_key: str,
    ) -> ExternalCalendarEvent:
        url = self._event_url(calendar_id, event_id)

        payload = {
            "summary": event.title,
            "description": event.description,
            "location": event.location,
            "start": self._serialize_time(event.start),
            "end": self._serialize_time(event.end),
            "status": "confirmed",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                existing = await self._get_existing_event(
                    client=client,
                    calendar_id=calendar_id,
                    event_id=event_id,
                    idempotency_key=idempotency_key,
                )

                etag = existing.get("etag")

                if not isinstance(etag, str) or not etag:
                    raise GoogleCalendarEventError("Google event version is unavailable")

                headers = {
                    **self._headers(),
                    "If-Match": etag,
                }

                response = await client.patch(
                    url,
                    headers=headers,
                    json=payload,
                    params={
                        "sendUpdates": "none",
                    },
                )

                if response.status_code == 412:
                    raise GoogleCalendarRetryableError(
                        "Google event changed during synchronization"
                    )

                if response.status_code in (404, 410):
                    raise GoogleCalendarEventNotFoundError("Google event no longer exists")

                self._check_response(response)

                try:
                    data = response.json()
                except ValueError as error:
                    raise GoogleCalendarEventError("Invalid Google event response") from error

                if not isinstance(data, dict):
                    raise GoogleCalendarEventError("Invalid Google event response")

                self._verify_event_ownership(
                    data,
                    idempotency_key,
                )

                return self._to_external_event(
                    data=data,
                    calendar_id=calendar_id,
                    draft=event,
                )

        except httpx.TransportError as error:
            raise GoogleCalendarRetryableError("Unable to reach Google Calendar") from error

    async def delete_event(
        self,
        calendar_id: str,
        event_id: str,
        idempotency_key: str,
    ) -> None:
        url = self._event_url(calendar_id, event_id)

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                try:
                    existing = await self._get_existing_event(
                        client=client,
                        calendar_id=calendar_id,
                        event_id=event_id,
                        idempotency_key=idempotency_key,
                    )

                except GoogleCalendarEventNotFoundError:
                    return

                etag = existing.get("etag")

                if not isinstance(etag, str) or not etag:
                    raise GoogleCalendarEventError("Google event version is unavailable")

                response = await client.delete(
                    url,
                    headers={
                        **self._headers(),
                        "If-Match": etag,
                    },
                    params={
                        "sendUpdates": "none",
                    },
                )

                if response.status_code in (404, 410):
                    return

                if response.status_code == 412:
                    raise GoogleCalendarRetryableError(
                        "Google event changed during deletion"
                    )

                self._check_response(response)

        except httpx.TransportError as error:
            raise GoogleCalendarRetryableError(
                "Unable to reach Google Calendar"
            ) from error
