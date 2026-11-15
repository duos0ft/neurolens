import uuid
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.conversations import validate_mutation_csrf
from app.core.auth import get_current_employee
from app.core.database import get_db
from app.models.employee import Employee
from app.schemas.calendar.calendar_suggestions import (
    SaveReviewedCalendarEventsRequest,
)
from app.services.calendar.calendar_suggestions import (
    CalendarSuggestionAlreadySavedError,
    CalendarSuggestionNotFoundError,
    CalendarSuggestionService,
    InvalidCalendarSelectionError,
)

router = APIRouter(
    prefix="/calendar/suggestions",
    tags=["Calendar Suggestions"],
)


class SavedCalendarSuggestionResponse(BaseModel):
    suggestion_index: int
    event_id: uuid.UUID


class SavedCalendarSuggestionsResponse(BaseModel):
    saved: list[SavedCalendarSuggestionResponse]


class CalendarEventResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    event_type: str
    all_day: bool
    start_date: date | None
    end_date: date | None
    starts_at: datetime | None
    ends_at: datetime | None
    timezone: str
    source_message_id: uuid.UUID | None
    source_suggestion_index: int | None
    created_at: datetime
    updated_at: datetime


def get_calendar_suggestion_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CalendarSuggestionService:
    return CalendarSuggestionService(db=db)


@router.get(
    "/{message_id}/saved",
    response_model=SavedCalendarSuggestionsResponse,
)
async def get_saved_calendar_suggestions(
    message_id: uuid.UUID,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[
        CalendarSuggestionService,
        Depends(get_calendar_suggestion_service),
    ],
) -> SavedCalendarSuggestionsResponse:
    try:
        saved = await service.get_saved_suggestions(
            employee_id=employee.user_id,
            message_id=message_id,
        )

    except CalendarSuggestionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar suggestions not found",
        ) from error

    return SavedCalendarSuggestionsResponse(
        saved=[
            SavedCalendarSuggestionResponse(
                suggestion_index=index,
                event_id=event_id,
            )
            for index, event_id in saved
        ],
    )


@router.post(
    "/{message_id}/save",
    response_model=list[CalendarEventResponse],
)
async def save_reviewed_calendar_suggestions(
    message_id: uuid.UUID,
    payload: SaveReviewedCalendarEventsRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[
        CalendarSuggestionService,
        Depends(get_calendar_suggestion_service),
    ],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> list[CalendarEventResponse]:
    try:
        events = await service.save_reviewed_suggestions(
            employee_id=employee.user_id,
            message_id=message_id,
            reviewed_events=payload.events,
        )

    except CalendarSuggestionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar suggestions not found",
        ) from error

    except InvalidCalendarSelectionError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    except CalendarSuggestionAlreadySavedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return [
        CalendarEventResponse.model_validate(
            event,
            from_attributes=True,
        )
        for event in events
    ]
