from datetime import date, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_employee
from app.core.database import get_db
from app.models.employee import Employee
from app.schemas.calendar.calendar import CalendarEntriesResponse
from app.services.calendar.calendar import CalendarService

MAX_CALENDAR_RANGE_DAYS = 366

router = APIRouter(
    prefix="/calendar",
    tags=["Calendar"],
)


def get_calendar_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CalendarService:
    return CalendarService(db=db)


@router.get(
    "/entries",
    response_model=CalendarEntriesResponse,
    status_code=status.HTTP_200_OK,
)
async def get_calendar_entries(
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[CalendarService, Depends(get_calendar_service)],
    start: Annotated[date, Query()],
    end: Annotated[date, Query()],
    calendar_timezone: Annotated[
        str,
        Query(alias="timezone"),
    ] = "UTC",
) -> CalendarEntriesResponse:
    if end <= start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="End date must be after start date",
        )
    if end - start > timedelta(days=MAX_CALENDAR_RANGE_DAYS):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Calendar date range cannot exceed {MAX_CALENDAR_RANGE_DAYS} days",
        )

    try:
        ZoneInfo(calendar_timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid calendar timezone",
        ) from error

    entries = await service.get_entries(
        employee_id=employee.user_id,
        start=start,
        end=end,
        calendar_timezone=calendar_timezone,
    )

    return CalendarEntriesResponse(
        entries=entries,
    )
