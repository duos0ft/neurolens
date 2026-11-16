import uuid
from urllib.parse import quote

import httpx

from app.core.settings import settings


class PolicyStorageError(Exception):
    pass


class PolicyStorageNotFoundError(PolicyStorageError):
    pass


class PolicyStorageService:
    def __init__(self) -> None:
        self.base_url = settings.supabase_url.rstrip("/")
        self.bucket = settings.supabase_policy_bucket
        self.api_key = settings.supabase_secret_key

    def _object_url(self, path: str) -> str:
        return (
            f"{self.base_url}/storage/v1/object/"
            f"{quote(self.bucket, safe='')}/"
            f"{quote(path, safe='/')}"
        )

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.api_key,
        }

    async def upload_pdf(
        self,
        document_id: uuid.UUID,
        version_id: uuid.UUID,
        content: bytes,
    ) -> str:
        if not content or not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF file")

        path = f"policies/{document_id}/versions/{version_id}.pdf"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self._object_url(path),
                    headers={
                        **self._headers(),
                        "Content-Type": "application/pdf",
                        "x-upsert": "false",
                    },
                    content=content,
                )

                response.raise_for_status()

        except httpx.HTTPError as error:
            raise PolicyStorageError("Unable to upload policy document") from error

        return path

    async def delete_pdf(self, path: str) -> None:
        if not path.startswith("policies/"):
            raise ValueError("Invalid policy storage path")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.delete(
                    self._object_url(path),
                    headers=self._headers(),
                )

                if response.status_code == 404:
                    return

                response.raise_for_status()

        except httpx.HTTPError as error:
            raise PolicyStorageError("Unable to delete policy document") from error

    async def download_pdf(self, path: str) -> bytes:
        if not path.startswith("policies/") or not path.endswith(".pdf"):
            raise ValueError("Invalid policy storage path")

        max_size = 10 * 1024 * 1024

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "GET",
                    self._object_url(path),
                    headers=self._headers(),
                ) as response:
                    if response.status_code == 404:
                        raise PolicyStorageNotFoundError("Policy PDF not found")

                    response.raise_for_status()

                    content = bytearray()

                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)

                        if len(content) > max_size:
                            raise PolicyStorageError("Policy PDF exceeds the maximum size")

        except PolicyStorageError:
            raise

        except httpx.HTTPError as error:
            raise PolicyStorageError("Unable to retrieve policy PDF") from error

        return bytes(content)
