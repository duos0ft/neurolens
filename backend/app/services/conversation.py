import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.capabilities.text_generation import GenerationMessage
from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage
from app.services.assistant import AssistantService

MAX_HISTORY_MESSAGES = 20


class ConversationService:
    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

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
        assistant: AssistantService,
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

            return user_message, assistant_message

        except Exception:
            await self.db.rollback()
            raise

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
