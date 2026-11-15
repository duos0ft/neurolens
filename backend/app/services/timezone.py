import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_settings import ApplicationSettings
from app.models.employee_profile import EmployeeProfile


DEFAULT_TIMEZONE = "UTC"


def validate_timezone(value: str) -> str:
    timezone = value.strip()

    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError("Invalid IANA timezone") from error

    return timezone


class TimezoneService:
    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def get_organization_timezone(self) -> str:
        timezone = await self.db.scalar(
            select(ApplicationSettings.default_timezone).where(ApplicationSettings.id == 1)
        )

        if timezone is None:
            return DEFAULT_TIMEZONE

        return validate_timezone(timezone)

    async def get_effective_timezone(
        self,
        employee_id: uuid.UUID,
    ) -> str:
        employee_timezone = await self.db.scalar(
            select(EmployeeProfile.timezone).where(EmployeeProfile.user_id == employee_id)
        )

        if employee_timezone is not None:
            return validate_timezone(employee_timezone)

        return await self.get_organization_timezone()
