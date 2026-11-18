import httpx

from app.core.settings import settings
from app.schemas.email.resend import (
    ResendSendEmailRequest,
    ResendSendEmailResponse,
)


class ResendAPIError(Exception):
    def __init__(self, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__("Resend email delivery request failed")


class ResendService:
    def __init__(self) -> None:
        self.base_url = "https://api.resend.com"
        self.api_key = settings.resend_api_key

    async def send_email(
        self,
        request: ResendSendEmailRequest,
        idempotency_key: str,
    ) -> ResendSendEmailResponse:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "Idempotency-Key": idempotency_key,
                    },
                    json=request.model_dump(
                        mode="json",
                        by_alias=True,
                        exclude_none=True,
                    ),
                )

                response.raise_for_status()

                return ResendSendEmailResponse.model_validate(response.json())

        except httpx.HTTPStatusError as error:
            raise ResendAPIError(
                status_code=error.response.status_code,
            ) from error

        except httpx.RequestError as error:
            raise ResendAPIError() from error
