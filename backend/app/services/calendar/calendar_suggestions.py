import uuid

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.capabilities.calendar_extraction import CalendarExtractionResult
from app.models.calendar_event import CalendarEvent
from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage
from app.schemas.calendar.calendar_suggestions import ReviewedCalendarEvent
from app.services.calendar.calendar_extraction import (
    normalize_calendar_extraction_data,
)


class CalendarSuggestionNotFoundError(Exception):
    pass


class InvalidCalendarSelectionError(Exception):
    pass


class CalendarSuggestionAlreadySavedError(Exception):
    pass


class CalendarSuggestionService:
    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def _get_source_message(
        self,
        employee_id: uuid.UUID,
        message_id: uuid.UUID,
        lock: bool = False,
    ) -> ConversationMessage:
        query = (
            select(ConversationMessage)
            .join(
                Conversation,
                Conversation.id == ConversationMessage.conversation_id,
            )
            .where(
                ConversationMessage.id == message_id,
                ConversationMessage.role == "assistant",
                Conversation.employee_id == employee_id,
            )
        )

        if lock:
            query = query.with_for_update(
                of=ConversationMessage,
            )

        message = await self.db.scalar(query)

        if message is None:
            raise CalendarSuggestionNotFoundError("Calendar suggestions not found")

        suggestions = message.calendar_suggestions

        if not isinstance(suggestions, dict) or not isinstance(suggestions.get("events"), list):
            raise CalendarSuggestionNotFoundError("Calendar suggestions not found")

        return message

    def _get_original_events(
        self,
        message: ConversationMessage,
    ) -> CalendarExtractionResult:
        suggestions = message.calendar_suggestions

        normalized = normalize_calendar_extraction_data(
            {
                "events": suggestions["events"],
            }
        )

        try:
            return CalendarExtractionResult.model_validate(
                normalized,
            )
        except ValidationError as error:
            raise InvalidCalendarSelectionError(
                "Stored calendar suggestions are invalid"
            ) from error

    async def get_saved_suggestions(
        self,
        employee_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> list[tuple[int, uuid.UUID]]:
        await self._get_source_message(
            employee_id=employee_id,
            message_id=message_id,
        )

        result = await self.db.execute(
            select(
                CalendarEvent.source_suggestion_index,
                CalendarEvent.id,
            )
            .where(
                CalendarEvent.employee_id == employee_id,
                CalendarEvent.source_message_id == message_id,
                CalendarEvent.source_suggestion_index.is_not(None),
            )
            .order_by(
                CalendarEvent.source_suggestion_index,
            )
        )

        return [(suggestion_index, event_id) for suggestion_index, event_id in result.all()]

    async def save_reviewed_suggestions(
        self,
        employee_id: uuid.UUID,
        message_id: uuid.UUID,
        reviewed_events: list[ReviewedCalendarEvent],
    ) -> list[CalendarEvent]:
        try:
            source_message = await self._get_source_message(
                employee_id=employee_id,
                message_id=message_id,
                lock=True,
            )

            extraction = self._get_original_events(
                source_message,
            )

            if not reviewed_events:
                raise InvalidCalendarSelectionError("At least one calendar event must be selected")

            selected_indices = [event.suggestion_index for event in reviewed_events]

            if len(selected_indices) != len(set(selected_indices)):
                raise InvalidCalendarSelectionError("Duplicate calendar suggestion indices")

            if any(index < 0 or index >= len(extraction.events) for index in selected_indices):
                raise InvalidCalendarSelectionError("Invalid calendar suggestion index")

            existing = await self.db.scalars(
                select(
                    CalendarEvent.source_suggestion_index,
                ).where(
                    CalendarEvent.employee_id == employee_id,
                    CalendarEvent.source_message_id == message_id,
                    CalendarEvent.source_suggestion_index.in_(
                        selected_indices,
                    ),
                )
            )

            if existing.first() is not None:
                raise CalendarSuggestionAlreadySavedError(
                    "One or more calendar suggestions have already been saved"
                )

            events = [
                CalendarEvent(
                    employee_id=employee_id,
                    title=event.title.strip(),
                    description=event.description,
                    event_type=event.event_type.value,
                    all_day=event.all_day,
                    start_date=event.start_date,
                    end_date=event.end_date,
                    starts_at=event.starts_at,
                    ends_at=event.ends_at,
                    timezone=event.timezone,
                    source_message_id=message_id,
                    source_suggestion_index=event.suggestion_index,
                )
                for event in reviewed_events
            ]

            self.db.add_all(events)

            await self.db.commit()

            for event in events:
                await self.db.refresh(event)

            return events

        except Exception:
            await self.db.rollback()
            raise
