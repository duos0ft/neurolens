import logging
import uuid
from datetime import datetime
from datetime import timezone as datetime_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.capabilities.text_generation import (
    GenerationMessage,
    TextGenerationProvider,
    TextGenerationResponse,
)
from app.ai.capabilities.types import AICapability
from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage
from app.services.assistant_execution_result import AssistantExecutionResult
from app.services.assistant_protocol import AssistantProtocol
from app.services.capability_classifier import CapabilityClassification
from app.services.conversation_capability_metadata import (
    ConversationCapabilityMetadata,
)
from app.services.conversation_title import ConversationTitleService
from app.services.orchestrated_assistant import OrchestratedAssistantService
from app.services.task_source_resolver import (
    TaskSourceResolutionError,
    TaskSourceResolver,
)


logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20


class TaskSourceAmbiguityError(Exception):
    pass


class ConversationService:
    def __init__(
        self,
        db: AsyncSession,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        title_provider: TextGenerationProvider | None = None,
    ) -> None:
        self.db = db
        self.session_factory = session_factory
        self.title_provider = title_provider

    async def create(
        self,
        employee_id: uuid.UUID,
        title: str | None = None,
    ) -> Conversation:
        conversation = Conversation(
            employee_id=employee_id,
            title=title.strip() or None if title is not None else None,
        )

        self.db.add(conversation)

        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def list(
        self,
        employee_id: uuid.UUID,
    ) -> list[Conversation]:
        result = await self.db.scalars(
            select(Conversation)
            .where(
                Conversation.employee_id == employee_id,
            )
            .order_by(
                Conversation.updated_at.desc(),
                Conversation.id.desc(),
            )
        )

        return list(result.all())

    async def get(
        self,
        employee_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        return await self.db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.employee_id == employee_id,
            )
        )

    async def get_messages(
        self,
        employee_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> list[ConversationMessage] | None:
        conversation = await self.get(
            employee_id=employee_id,
            conversation_id=conversation_id,
        )

        if conversation is None:
            return None

        result = await self.db.scalars(
            select(ConversationMessage)
            .where(
                ConversationMessage.conversation_id == conversation_id,
            )
            .order_by(
                ConversationMessage.sequence_number.asc(),
            )
        )

        return list(result.all())

    async def send_message(
        self,
        employee_id: uuid.UUID,
        conversation_id: uuid.UUID,
        content: str,
        assistant: AssistantProtocol,
        timezone: str,
    ) -> tuple[ConversationMessage, ConversationMessage] | None:
        content = content.strip()

        if not content:
            raise ValueError("Message cannot be empty")

        try:
            ZoneInfo(timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError("Invalid calendar timezone") from error

        message_received_at = datetime.now(datetime_timezone.utc)

        try:
            conversation = await self.db.scalar(
                select(Conversation)
                .where(
                    Conversation.id == conversation_id,
                    Conversation.employee_id == employee_id,
                )
                .with_for_update()
            )

            if conversation is None:
                await self.db.rollback()
                return None

            result = await self.db.scalars(
                select(ConversationMessage)
                .where(
                    ConversationMessage.conversation_id == conversation_id,
                )
                .order_by(
                    ConversationMessage.sequence_number.desc(),
                )
                .limit(MAX_HISTORY_MESSAGES)
            )

            history_messages = list(reversed(result.all()))

            history = [
                GenerationMessage(
                    role=message.role,
                    content=message.content,
                )
                for message in history_messages
            ]

            execution_result: AssistantExecutionResult | None = None

            if isinstance(assistant, OrchestratedAssistantService):
                classification = await assistant.orchestrator.classify(
                    message=content,
                    history=history,
                )

                extraction_capabilities = {
                    AICapability.TASK_EXTRACTION,
                    AICapability.CALENDAR_EXTRACTION,
                }

                selected_extractions = [
                    intent
                    for intent in classification.intents
                    if intent.capability in extraction_capabilities
                ]

                if selected_extractions:
                    if AICapability.POLICY_QUESTION in classification.capabilities:
                        execution_result = AssistantExecutionResult(
                            response=TextGenerationResponse(
                                content=(
                                    "I can't extract tasks or calendar events "
                                    "from a request mixed with unverified "
                                    "company-policy information. Please "
                                    "provide the assignment or scheduling "
                                    "details separately."
                                ),
                                model="neurolens",
                            ),
                            capabilities=(AICapability.POLICY_QUESTION,),
                        )

                    else:
                        extraction_results: list[AssistantExecutionResult] = []

                        candidates = [
                            message
                            for message in history_messages
                            if message.role == "user" and message.content.strip()
                        ]

                        for intent in selected_extractions:
                            source_message_id = None
                            reference_datetime = message_received_at

                            if intent.source_scope == "previous":
                                if not candidates:
                                    raise TaskSourceAmbiguityError(
                                        "No earlier employee message is available"
                                    )

                                resolver = TaskSourceResolver(
                                    registry=assistant.orchestrator.registry,
                                )

                                source_message_id = await resolver.resolve(
                                    request=(
                                        f"{content}\n\nRequested information: {intent.instruction}"
                                    ),
                                    messages=candidates,
                                )

                                if source_message_id is None:
                                    raise TaskSourceAmbiguityError(
                                        "Unable to identify the earlier message"
                                    )

                                source_message = next(
                                    (
                                        message
                                        for message in candidates
                                        if message.id == source_message_id
                                    ),
                                    None,
                                )

                                if source_message is None:
                                    raise TaskSourceResolutionError(
                                        "Resolved source is not an authorized message"
                                    )

                                source_text = source_message.content
                                reference_datetime = source_message.created_at

                            else:
                                source_text = intent.source_text or content

                            if intent.capability == AICapability.TASK_EXTRACTION:
                                extraction_result = await assistant.extract_tasks(
                                    source_text=source_text,
                                    source_message_id=source_message_id,
                                    reference_datetime=reference_datetime,
                                    timezone=timezone,
                                )

                                extraction_results.append(extraction_result)

                            elif intent.capability == AICapability.CALENDAR_EXTRACTION:
                                extraction_result = await assistant.extract_calendar(
                                    source_text=source_text,
                                    reference_datetime=reference_datetime,
                                    timezone=timezone,
                                    source_message_id=source_message_id,
                                )

                                extraction_results.append(extraction_result)

                        additional_intents = [
                            intent
                            for intent in classification.intents
                            if intent.capability not in extraction_capabilities
                            and intent.capability != AICapability.GENERAL_CONVERSATION
                        ]

                        additional_result: AssistantExecutionResult | None = None

                        if additional_intents:
                            additional_result = await assistant.execute(
                                message=content,
                                history=history,
                                classification=CapabilityClassification(
                                    intents=additional_intents,
                                ),
                            )

                        response_parts: list[str] = []

                        if additional_result is not None:
                            response_parts.append(
                                additional_result.response.content,
                            )

                        response_parts.extend(
                            result.response.content for result in extraction_results
                        )

                        response_content = "\n\n".join(
                            part.strip() for part in response_parts if part.strip()
                        )

                        capabilities = [
                            capability
                            for result in extraction_results
                            for capability in result.capabilities
                        ]

                        sources = ()

                        if additional_result is not None:
                            capabilities.extend(
                                additional_result.capabilities,
                            )
                            sources = additional_result.sources

                        execution_result = AssistantExecutionResult(
                            response=TextGenerationResponse(
                                content=response_content,
                                model="neurolens-combined-assistance",
                            ),
                            capabilities=tuple(dict.fromkeys(capabilities)),
                            sources=sources,
                            task_suggestions=next(
                                (
                                    result.task_suggestions
                                    for result in extraction_results
                                    if result.task_suggestions is not None
                                ),
                                None,
                            ),
                            calendar_suggestions=next(
                                (
                                    result.calendar_suggestions
                                    for result in extraction_results
                                    if result.calendar_suggestions is not None
                                ),
                                None,
                            ),
                            clarifications=(
                                additional_result.clarifications
                                if additional_result is not None
                                else None
                            ),
                        )

                else:
                    execution_result = await assistant.execute(
                        message=content,
                        history=history,
                        classification=classification,
                    )

            else:
                execute = getattr(assistant, "execute", None)

                if callable(execute):
                    execution_result = await execute(
                        message=content,
                        history=history,
                    )

                else:
                    response = await assistant.respond(
                        message=content,
                        history=history,
                    )

            capability_metadata = None
            task_suggestions = None
            calendar_suggestions = None
            clarifications = None

            if execution_result is not None:
                response = execution_result.response

                if execution_result.capabilities:
                    capability_metadata = ConversationCapabilityMetadata(
                        capabilities=execution_result.capabilities,
                        sources=execution_result.sources,
                    ).to_dict()

                if execution_result.task_suggestions is not None:
                    suggestions = execution_result.task_suggestions

                    task_suggestions = {
                        "version": 1,
                        "source_message_id": (
                            str(suggestions.source_message_id)
                            if suggestions.source_message_id is not None
                            else None
                        ),
                        "tasks": [
                            task.model_dump(mode="json") for task in suggestions.extraction.tasks
                        ],
                    }

                if execution_result.calendar_suggestions is not None:
                    suggestions = execution_result.calendar_suggestions

                    calendar_suggestions = {
                        "version": 1,
                        "source_message_id": (
                            str(suggestions.source_message_id)
                            if suggestions.source_message_id is not None
                            else None
                        ),
                        "events": [
                            event.model_dump(mode="json") for event in suggestions.extraction.events
                        ],
                    }

                if (
                    execution_result.clarifications is not None
                    and execution_result.clarifications.questions
                ):
                    clarifications = {
                        "version": 1,
                        "questions": list(execution_result.clarifications.questions),
                    }

            last_sequence = await self.db.scalar(
                select(func.max(ConversationMessage.sequence_number)).where(
                    ConversationMessage.conversation_id == conversation_id,
                )
            )

            next_sequence = (last_sequence or 0) + 1

            should_generate_title = (
                last_sequence is None
                and conversation.title is None
                and self.title_provider is not None
                and self.session_factory is not None
            )

            user_message = ConversationMessage(
                conversation_id=conversation_id,
                sequence_number=next_sequence,
                role="user",
                content=content,
                created_at=message_received_at,
            )

            assistant_message = ConversationMessage(
                conversation_id=conversation_id,
                sequence_number=next_sequence + 1,
                role="assistant",
                content=response.content,
                model=response.model,
                capability_metadata=capability_metadata,
                task_suggestions=task_suggestions,
                calendar_suggestions=calendar_suggestions,
                clarifications=clarifications,
            )

            self.db.add_all(
                [
                    user_message,
                    assistant_message,
                ]
            )

            await self.db.commit()

            await self.db.refresh(user_message)
            await self.db.refresh(assistant_message)

        except Exception:
            await self.db.rollback()
            raise

        if should_generate_title:
            await self._generate_title(
                employee_id=employee_id,
                conversation_id=conversation_id,
                user_message=content,
                assistant_response=response.content,
            )

        return user_message, assistant_message

    async def _generate_title(
        self,
        employee_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_message: str,
        assistant_response: str,
    ) -> None:
        if self.session_factory is None:
            logger.warning(
                "Title generation skipped for conversation %s: session factory is not configured",
                conversation_id,
            )
            return

        if self.title_provider is None:
            logger.debug(
                "Title generation skipped for conversation %s: title provider is not configured",
                conversation_id,
            )
            return

        try:
            title_service = ConversationTitleService(
                provider=self.title_provider,
            )

            title = await title_service.generate(
                user_message=user_message,
                assistant_response=assistant_response,
            )

            if not title:
                return

        except Exception:
            logger.warning(
                "Unable to generate title for conversation %s",
                conversation_id,
                exc_info=True,
            )
            return

        try:
            async with self.session_factory() as title_db:
                async with title_db.begin():
                    await title_db.execute(
                        update(Conversation)
                        .where(
                            Conversation.id == conversation_id,
                            Conversation.employee_id == employee_id,
                            Conversation.title.is_(None),
                        )
                        .values(
                            title=title,
                        )
                    )

        except Exception:
            logger.warning(
                "Unable to save title for conversation %s",
                conversation_id,
                exc_info=True,
            )

    async def rename(
        self,
        employee_id: uuid.UUID,
        conversation_id: uuid.UUID,
        title: str,
    ) -> Conversation | None:
        title = " ".join(title.split())

        if not title or len(title) > 100:
            raise ValueError("Conversation title must be between 1 and 100 characters")

        conversation = await self.get(
            employee_id=employee_id,
            conversation_id=conversation_id,
        )

        if conversation is None:
            return None

        conversation.title = title

        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def delete(
            self,
            employee_id: uuid.UUID,
            conversation_id: uuid.UUID,
    ) -> bool:
        conversation = await self.get(
            employee_id=employee_id,
            conversation_id=conversation_id,
        )

        if conversation is None:
            return False

        await self.db.delete(conversation)
        await self.db.commit()

        return True
