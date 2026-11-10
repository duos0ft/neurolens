import uuid

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.capabilities.task_extraction import TaskExtractionResult
from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage
from app.models.subtask import Subtask
from app.models.task import Task


class TaskSuggestionNotFoundError(Exception):
    pass


class InvalidTaskSelectionError(Exception):
    pass


class TaskService:
    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def save_suggestions(
        self,
        employee_id: uuid.UUID,
        message_id: uuid.UUID,
        selected_indices: list[int],
    ) -> list[Task]:
        if not selected_indices:
            raise InvalidTaskSelectionError("At least one task suggestion must be selected")

        if any(type(index) is not int or index < 0 for index in selected_indices):
            raise InvalidTaskSelectionError("Invalid task suggestion index")

        if len(selected_indices) != len(set(selected_indices)):
            raise InvalidTaskSelectionError("Duplicate task suggestion indices are not allowed")

        try:
            result = await self.db.execute(
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
                .with_for_update(of=ConversationMessage)
            )

            source_message = result.scalar_one_or_none()

            if source_message is None:
                raise TaskSuggestionNotFoundError("Task suggestions not found")

            suggestions = source_message.task_suggestions

            if (
                not isinstance(suggestions, dict)
                or suggestions.get("version") != 1
                or not isinstance(suggestions.get("tasks"), list)
            ):
                raise TaskSuggestionNotFoundError("Task suggestions not found")

            try:
                extraction = TaskExtractionResult.model_validate(
                    {
                        "tasks": suggestions["tasks"],
                    }
                )
            except ValidationError as error:
                raise InvalidTaskSelectionError("Stored task suggestions are invalid") from error

            if any(index >= len(extraction.tasks) for index in selected_indices):
                raise InvalidTaskSelectionError("Selected task suggestion does not exist")

            saved_tasks: list[Task] = []

            for index in selected_indices:
                suggestion = extraction.tasks[index]

                statement = (
                    insert(Task)
                    .values(
                        employee_id=employee_id,
                        title=suggestion.title,
                        description=suggestion.description,
                        status="todo",
                        priority=suggestion.priority,
                        due_date=suggestion.due_date,
                        source_message_id=source_message.id,
                        source_suggestion_index=index,
                    )
                    .on_conflict_do_nothing(
                        constraint="tasks_employee_source_suggestion_unique",
                    )
                    .returning(Task.id)
                )

                task_id = await self.db.scalar(statement)

                if task_id is not None:
                    for sort_order, subtask in enumerate(suggestion.subtasks):
                        self.db.add(
                            Subtask(
                                task_id=task_id,
                                title=subtask.title,
                                completed=False,
                                sort_order=sort_order,
                            )
                        )

                else:
                    task_id = await self.db.scalar(
                        select(Task.id).where(
                            Task.employee_id == employee_id,
                            Task.source_message_id == source_message.id,
                            Task.source_suggestion_index == index,
                        )
                    )

                    if task_id is None:
                        raise RuntimeError("Unable to retrieve saved task suggestion")

                task = await self.db.get(Task, task_id)

                if task is None:
                    raise RuntimeError("Unable to retrieve saved task")

                saved_tasks.append(task)

            await self.db.commit()

            for task in saved_tasks:
                await self.db.refresh(task)

            return saved_tasks

        except Exception:
            await self.db.rollback()
            raise
