import logging
import uuid

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
from app.services.conversation_capability_metadata import (
    ConversationCapabilityMetadata,
)
from app.services.conversation_title import ConversationTitleService
from app.services.orchestrated_assistant import OrchestratedAssistantService
from app.services.task_source_resolver import TaskSourceResolutionError, TaskSourceResolver

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
    ) -> tuple[ConversationMessage, ConversationMessage] | None:
        content = content.strip()

        if not content:
            raise ValueError("Message cannot be empty")

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

            capability_metadata = None
            task_suggestions = None

            if isinstance(assistant, OrchestratedAssistantService):
                classification = await assistant.orchestrator.classify(
                    message=content,
                    history=history,
                )

                if AICapability.TASK_EXTRACTION in classification.capabilities:
                    if AICapability.POLICY_QUESTION in classification.capabilities:
                        execution_result = AssistantExecutionResult(
                            response=TextGenerationResponse(
                                content=(
                                    "I can't extract tasks from a request "
                                    "mixed with unverified company-policy "
                                    "information. Please provide the "
                                    "workplace assignment separately."
                                ),
                                model="neurolens",
                            ),
                            capabilities=(AICapability.POLICY_QUESTION,),
                        )
                    else:
                        extraction_intent = next(
                            intent
                            for intent in classification.intents
                            if intent.capability == AICapability.TASK_EXTRACTION
                        )

                        source_text = extraction_intent.source_text
                        source_message_id = None

                        if source_text is None:
                            candidates = [
                                message
                                for message in history_messages
                                if message.role == "user" and message.content.strip()
                            ]

                            if not candidates:
                                raise TaskSourceAmbiguityError(
                                    "No earlier workplace message is available"
                                )

                            resolver = TaskSourceResolver(
                                registry=assistant.orchestrator.registry,
                            )

                            source_message_id = await resolver.resolve(
                                request=content,
                                messages=candidates,
                            )

                            if source_message_id is None:
                                raise TaskSourceAmbiguityError(
                                    "Unable to identify the earlier workplace message"
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

                        execution_result = await assistant.extract_tasks(
                            source_text=source_text,
                            source_message_id=source_message_id,
                        )

                else:
                    execution_result = await assistant.execute(
                        message=content,
                        history=history,
                        classification=classification,
                    )

                response = execution_result.response

                if execution_result.capabilities:
                    capability_metadata = ConversationCapabilityMetadata.from_execution_result(
                        execution_result
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

            else:
                execute = getattr(assistant, "execute", None)

                if callable(execute):
                    execution_result: AssistantExecutionResult = await execute(
                        message=content,
                        history=history,
                    )

                    response = execution_result.response

                    if execution_result.capabilities:
                        capability_metadata = ConversationCapabilityMetadata.from_execution_result(
                            execution_result
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
                                task.model_dump(mode="json")
                                for task in suggestions.extraction.tasks
                            ],
                        }
                else:
                    response = await assistant.respond(
                        message=content,
                        history=history,
                    )

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
            )

            assistant_message = ConversationMessage(
                conversation_id=conversation_id,
                sequence_number=next_sequence + 1,
                role="assistant",
                content=response.content,
                model=response.model,
                capability_metadata=capability_metadata,
                task_suggestions=task_suggestions,
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
