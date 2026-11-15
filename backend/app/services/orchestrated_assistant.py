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
    AssistantClarifications,
)
from app.services.assistant_orchestrator import AssistantOrchestrator
from app.services.assistant_response_composer import AssistantResponseComposer
from app.services.calendar.calendar_extraction import CalendarExtractionService
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

        questions = tuple(
            question
            for result in results
            if result.structured_explanation is not None
            for question in result.structured_explanation.clarification_questions
        )

        clarifications = (
            AssistantClarifications(questions=tuple(dict.fromkeys(questions)))
            if questions and self.orchestrator.config.highlight_ambiguity
            else None
        )

        return AssistantExecutionResult(
            response=self.composer.compose(
                results,
                config=self.orchestrator.config,
            ),
            capabilities=tuple(result.capability for result in results),
            sources=tuple(result.source for result in results if result.source is not None),
            clarifications=clarifications,
        )

    async def extract_tasks(
        self,
        source_text: str,
        source_message_id: uuid.UUID | None = None,
        reference_datetime: datetime | None = None,
        timezone: str | None = None,
    ) -> AssistantExecutionResult:
        extraction_service = TaskExtractionService(
            registry=self.orchestrator.registry,
        )

        extraction = await extraction_service.extract(
            text=source_text,
            reference_datetime=reference_datetime,
            timezone=timezone,
        )

        count = len(extraction.tasks)

        content = (
            "I found a task for you."
            if count == 1
            else f"I found {count} tasks for you."
            if count > 1
            else ""
        )

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

        count = len(extraction.events)

        content = (
            "I found a calendar event."
            if count == 1
            else f"I found {count} calendar events."
            if count > 1
            else ""
        )

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
