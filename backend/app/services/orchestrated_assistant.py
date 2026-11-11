import uuid
from datetime import datetime

from app.ai.capabilities.text_generation import (
    GenerationMessage,
    TextGenerationResponse,
)
from app.ai.capabilities.types import AICapability
from app.services.assistant_execution_result import (
    AssistantCalendarSuggestions,
    AssistantExecutionResult,
    AssistantTaskSuggestions,
)
from app.services.assistant_orchestrator import AssistantOrchestrator
from app.services.assistant_response_composer import AssistantResponseComposer
from app.services.calendar_extraction import CalendarExtractionService
from app.services.capability_classifier import CapabilityClassification
from app.services.task_extraction import TaskExtractionService


class OrchestratedAssistantService:
    def __init__(
        self,
        orchestrator: AssistantOrchestrator,
        composer: AssistantResponseComposer,
    ) -> None:
        self.orchestrator = orchestrator
        self.composer = composer

    async def execute(
        self,
        message: str,
        history: list[GenerationMessage] | None = None,
        classification: CapabilityClassification | None = None,
    ) -> AssistantExecutionResult:
        results = await self.orchestrator.respond(
            message=message,
            history=history,
            classification=classification,
        )

        return AssistantExecutionResult(
            response=self.composer.compose(
                results,
                config=self.orchestrator.config,
            ),
            capabilities=tuple(result.capability for result in results),
            sources=tuple(result.source for result in results if result.source is not None),
        )

    async def extract_tasks(
        self,
        source_text: str,
        source_message_id: uuid.UUID | None = None,
    ) -> AssistantExecutionResult:
        extraction_service = TaskExtractionService(
            registry=self.orchestrator.registry,
        )

        extraction = await extraction_service.extract(
            text=source_text,
        )

        if extraction.tasks:
            content = (
                f"I found {len(extraction.tasks)} possible "
                "task suggestions. Review them below and "
                "choose which ones you'd like to keep."
            )
        else:
            content = "I couldn't identify any actionable tasks in that message."

        return AssistantExecutionResult(
            response=TextGenerationResponse(
                content=content,
                model="neurolens-task-extraction",
            ),
            capabilities=(AICapability.TASK_EXTRACTION,),
            task_suggestions=AssistantTaskSuggestions(
                source_message_id=source_message_id,
                extraction=extraction,
            ),
        )

    async def extract_calendar(
        self,
        source_text: str,
        reference_datetime: datetime,
        timezone: str,
        source_message_id: uuid.UUID | None = None,
    ) -> AssistantExecutionResult:
        extraction_service = CalendarExtractionService(
            registry=self.orchestrator.registry,
        )

        extraction = await extraction_service.extract(
            text=source_text,
            reference_datetime=reference_datetime,
            timezone=timezone,
        )

        if extraction.events:
            content = (
                f"I found {len(extraction.events)} possible "
                "calendar suggestions. Review them below "
                "before adding them to your calendar."
            )
        else:
            content = "I couldn't identify any scheduled events in that message."

        return AssistantExecutionResult(
            response=TextGenerationResponse(
                content=content,
                model="neurolens-calendar-extraction",
            ),
            capabilities=(AICapability.CALENDAR_EXTRACTION,),
            calendar_suggestions=AssistantCalendarSuggestions(
                source_message_id=source_message_id,
                extraction=extraction,
            ),
        )

    async def respond(
        self,
        message: str,
        history: list[GenerationMessage] | None = None,
    ) -> TextGenerationResponse:
        result = await self.execute(
            message=message,
            history=history,
        )

        return result.response
