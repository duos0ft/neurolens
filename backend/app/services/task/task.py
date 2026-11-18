import uuid
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import ValidationError
from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.capabilities.task_extraction import TaskExtractionResult
from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage
from app.models.subtask import Subtask
from app.models.task import Task
from app.schemas.task.task import CreateSubtaskRequest, ReviewedTask, UpdateSubtaskRequest
from app.services.calendar.calendar_sync import CalendarSyncService


class TaskSuggestionNotFoundError(Exception):
    pass


class InvalidTaskSelectionError(Exception):
    pass


class TaskNotFoundError(Exception):
    pass


class SubtaskNotFoundError(Exception):
    pass


class InvalidSubtaskError(Exception):
    pass


def resolve_task_deadline(
    due_date: date | None,
    due_time: time | None,
    due_timezone: str | None,
    effective_timezone: str,
) -> tuple[date | None, time | None, str | None]:
    """
    Normalize a task deadline before database persistence.

    Date-only deadlines remain date-only.
    Timed deadlines always have an IANA timezone.
    """
    if due_date is None:
        if due_time is not None or due_timezone is not None:
            raise ValueError("A deadline time and timezone require a due date")

        return None, None, None

    if due_time is None:
        if due_timezone is not None:
            raise ValueError("A deadline timezone requires a time")

        return due_date, None, None

    if due_time.utcoffset() is not None:
        raise ValueError("Deadline time must not contain a UTC offset")

    if due_time.second != 0 or due_time.microsecond != 0:
        raise ValueError("Deadline time must have minute precision")

    resolved_timezone = due_timezone or effective_timezone

    try:
        zone = ZoneInfo(resolved_timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError("Invalid deadline timezone") from error

    # Reject nonexistent and ambiguous local wall-clock times.
    # These can occur during daylight-saving transitions.
    valid_instants = set()

    for fold in (0, 1):
        local_datetime = datetime.combine(
            due_date,
            due_time,
        ).replace(
            tzinfo=zone,
            fold=fold,
        )

        utc_datetime = local_datetime.astimezone(timezone.utc)
        round_trip = utc_datetime.astimezone(zone)

        if round_trip.date() == due_date and round_trip.time().replace(tzinfo=None) == due_time:
            valid_instants.add(utc_datetime)

    if not valid_instants:
        raise ValueError("Deadline time does not exist in the selected timezone")

    if len(valid_instants) > 1:
        raise ValueError("Deadline time is ambiguous in the selected timezone")

    return due_date, due_time, resolved_timezone


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
        *,
        effective_timezone: str,
    ) -> list[Task]:
        if not selected_indices:
            raise InvalidTaskSelectionError("At least one task suggestion must be selected")

        if any(type(index) is not int or index < 0 for index in selected_indices):
            raise InvalidTaskSelectionError("Invalid task suggestion index")

        if len(selected_indices) != len(set(selected_indices)):
            raise InvalidTaskSelectionError("Duplicate task suggestion indices are not allowed")

        sync_service = CalendarSyncService(self.db)

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

                due_date, due_time, due_timezone = resolve_task_deadline(
                    due_date=suggestion.due_date,
                    due_time=suggestion.due_time,
                    due_timezone=None,
                    effective_timezone=effective_timezone,
                )

                statement = (
                    insert(Task)
                    .values(
                        employee_id=employee_id,
                        title=suggestion.title,
                        description=suggestion.description,
                        status="todo",
                        priority=suggestion.priority,
                        due_date=due_date,
                        due_time=due_time,
                        due_timezone=due_timezone,
                        source_message_id=source_message.id,
                        source_suggestion_index=index,
                    )
                    .on_conflict_do_nothing(
                        constraint="tasks_employee_source_suggestion_unique",
                    )
                    .returning(Task.id)
                )

                task_id = await self.db.scalar(statement)
                was_created = task_id is not None

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

                if was_created and task.due_date is not None:
                    await sync_service.enqueue_upsert(
                        employee_id=employee_id,
                        source_type="task",
                        source_id=task.id,
                    )

                saved_tasks.append(task)

            await self.db.commit()

            for task in saved_tasks:
                await self.db.refresh(task)

            return saved_tasks

        except Exception:
            await self.db.rollback()
            raise

    async def save_reviewed_suggestions(
        self,
        employee_id: uuid.UUID,
        message_id: uuid.UUID,
        reviewed_tasks: list[ReviewedTask],
        *,
        effective_timezone: str,
    ) -> list[Task]:
        if not reviewed_tasks:
            raise InvalidTaskSelectionError("At least one reviewed task must be provided")

        indices = [task.suggestion_index for task in reviewed_tasks]

        if len(indices) != len(set(indices)):
            raise InvalidTaskSelectionError("Duplicate task suggestion indices are not allowed")

        if any(index < 0 for index in indices):
            raise InvalidTaskSelectionError("Invalid task suggestion index")

        sync_service = CalendarSyncService(self.db)

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

            if any(index >= len(extraction.tasks) for index in indices):
                raise InvalidTaskSelectionError("Selected task suggestion does not exist")

            saved_tasks: list[Task] = []

            for reviewed_task in reviewed_tasks:
                index = reviewed_task.suggestion_index

                due_date, due_time, due_timezone = resolve_task_deadline(
                    due_date=reviewed_task.due_date,
                    due_time=reviewed_task.due_time,
                    due_timezone=reviewed_task.due_timezone,
                    effective_timezone=effective_timezone,
                )

                statement = (
                    insert(Task)
                    .values(
                        employee_id=employee_id,
                        title=reviewed_task.title,
                        description=reviewed_task.description,
                        status="todo",
                        priority=reviewed_task.priority,
                        due_date=due_date,
                        due_time=due_time,
                        due_timezone=due_timezone,
                        source_message_id=source_message.id,
                        source_suggestion_index=index,
                    )
                    .on_conflict_do_nothing(
                        constraint="tasks_employee_source_suggestion_unique",
                    )
                    .returning(Task.id)
                )

                task_id = await self.db.scalar(statement)
                was_created = task_id is not None

                if task_id is not None:
                    for sort_order, subtask in enumerate(reviewed_task.subtasks):
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

                if was_created and task.due_date is not None:
                    await sync_service.enqueue_upsert(
                        employee_id=employee_id,
                        source_type="task",
                        source_id=task.id,
                    )

                saved_tasks.append(task)

            await self.db.commit()

            for task in saved_tasks:
                await self.db.refresh(task)

            return saved_tasks

        except Exception:
            await self.db.rollback()
            raise

    async def get_saved_suggestions(
        self,
        employee_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> list[tuple[int, uuid.UUID, bool, bool]]:
        result = await self.db.execute(
            select(ConversationMessage.id)
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

        if result.scalar_one_or_none() is None:
            raise TaskSuggestionNotFoundError("Task suggestions not found")

        result = await self.db.execute(
            select(
                Task.source_suggestion_index,
                Task.id,
                Task.archived_at,
                Task.deleted_at,
            )
            .where(
                Task.employee_id == employee_id,
                Task.source_message_id == message_id,
                Task.source_suggestion_index.is_not(None),
            )
            .order_by(Task.source_suggestion_index)
        )

        return [
            (
                suggestion_index,
                task_id,
                archived_at is not None,
                deleted_at is not None,
            )
            for suggestion_index, task_id, archived_at, deleted_at in result.all()
        ]

    async def get_task(
        self,
        employee_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> Task:
        task = await self.db.scalar(
            select(Task).where(
                Task.id == task_id,
                Task.employee_id == employee_id,
                Task.archived_at.is_(None),
                Task.deleted_at.is_(None),
            )
        )

        if task is None:
            raise TaskNotFoundError("Task not found")

        return task

    async def get_tasks(
        self,
        employee_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        priority: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        archived: bool = False,
    ) -> tuple[list[Task], int]:
        filters = [
            Task.employee_id == employee_id,
            Task.deleted_at.is_(None),
        ]

        if status is not None:
            filters.append(Task.status == status)

        if priority is not None:
            filters.append(Task.priority == priority)

        if archived:
            filters.append(Task.archived_at.is_not(None))
        else:
            filters.append(Task.archived_at.is_(None))

        total_items = await self.db.scalar(select(func.count(Task.id)).where(*filters)) or 0

        sort_columns = {
            "created_at": Task.created_at,
            "updated_at": Task.updated_at,
            "due_date": Task.due_date,
            "priority": case(
                (Task.priority == "high", 3),
                (Task.priority == "medium", 2),
                (Task.priority == "low", 1),
                else_=0,
            ),
        }

        sort_column = sort_columns[sort_by]

        ordering = (
            sort_column.asc().nulls_last()
            if sort_order == "asc"
            else sort_column.desc().nulls_last()
        )

        result = await self.db.scalars(
            select(Task)
            .where(*filters)
            .order_by(
                ordering,
                Task.id.desc(),
            )
            .limit(page_size)
            .offset((page - 1) * page_size)
        )

        return list(result.all()), total_items

    async def get_task_stats(
        self,
        employee_id: uuid.UUID,
    ) -> dict[str, int]:
        result = await self.db.execute(
            select(
                Task.status,
                func.count(Task.id),
            )
            .where(
                Task.employee_id == employee_id,
                Task.archived_at.is_(None),
                Task.deleted_at.is_(None),
            )
            .group_by(Task.status)
        )

        counts = {
            "todo": 0,
            "in_progress": 0,
            "completed": 0,
        }

        for task_status, count in result.all():
            counts[task_status] = count

        return counts

    async def update_status(
        self,
        employee_id: uuid.UUID,
        task_id: uuid.UUID,
        status: str,
    ) -> Task:
        try:
            task = await self.db.scalar(
                select(Task)
                .where(
                    Task.id == task_id,
                    Task.employee_id == employee_id,
                    Task.archived_at.is_(None),
                    Task.deleted_at.is_(None),
                )
                .with_for_update()
            )

            if task is None:
                raise TaskNotFoundError("Task not found")

            if task.status != status:
                task.status = status

                if status == "completed":
                    task.completed_at = datetime.now(timezone.utc)
                else:
                    task.completed_at = None

                if task.due_date is not None:
                    await CalendarSyncService(self.db).enqueue_upsert(
                        employee_id=employee_id,
                        source_type="task",
                        source_id=task.id,
                    )

                await self.db.commit()
                await self.db.refresh(task)

            return task

        except Exception:
            await self.db.rollback()
            raise

    async def create_task(
        self,
        employee_id: uuid.UUID,
        title: str,
        description: str | None,
        priority: str | None,
        due_date: date | None,
        subtasks: list[CreateSubtaskRequest],
        *,
        due_time: time | None = None,
        due_timezone: str | None = None,
        effective_timezone: str,
    ) -> Task:
        due_date, due_time, due_timezone = resolve_task_deadline(
            due_date=due_date,
            due_time=due_time,
            due_timezone=due_timezone,
            effective_timezone=effective_timezone,
        )

        try:
            task = Task(
                employee_id=employee_id,
                title=title,
                description=description,
                status="todo",
                priority=priority,
                due_date=due_date,
                due_time=due_time,
                due_timezone=due_timezone,
            )

            self.db.add(task)
            await self.db.flush()

            for sort_order, subtask in enumerate(subtasks):
                self.db.add(
                    Subtask(
                        task_id=task.id,
                        title=subtask.title,
                        completed=False,
                        sort_order=sort_order,
                    )
                )

            if task.due_date is not None:
                await CalendarSyncService(self.db).enqueue_upsert(
                    employee_id=employee_id,
                    source_type="task",
                    source_id=task.id,
                )

            await self.db.commit()
            await self.db.refresh(task)

            return task

        except Exception:
            await self.db.rollback()
            raise

    async def update_task(
        self,
        employee_id: uuid.UUID,
        task_id: uuid.UUID,
        title: str,
        description: str | None,
        priority: str | None,
        due_date: date | None,
        subtasks: list[UpdateSubtaskRequest] | None,
        *,
        due_time: time | None = None,
        due_timezone: str | None = None,
        effective_timezone: str,
    ) -> Task:
        due_date, due_time, due_timezone = resolve_task_deadline(
            due_date=due_date,
            due_time=due_time,
            due_timezone=due_timezone,
            effective_timezone=effective_timezone,
        )

        try:
            task = await self.db.scalar(
                select(Task)
                .where(
                    Task.id == task_id,
                    Task.employee_id == employee_id,
                    Task.archived_at.is_(None),
                    Task.deleted_at.is_(None),
                )
                .with_for_update()
            )

            if task is None:
                raise TaskNotFoundError("Task not found")

            calendar_details_changed = (
                task.title != title
                or task.description != description
                or task.due_date != due_date
                or task.due_time != due_time
                or task.due_timezone != due_timezone
            )

            existing_subtasks = {}

            if subtasks is not None:
                result = await self.db.scalars(
                    select(Subtask).where(Subtask.task_id == task_id).with_for_update()
                )

                existing_subtasks = {subtask.id: subtask for subtask in result.all()}

                submitted_ids = [subtask.id for subtask in subtasks if subtask.id is not None]

                if len(submitted_ids) != len(set(submitted_ids)):
                    raise InvalidSubtaskError("Duplicate subtask IDs are not allowed")

                if any(subtask_id not in existing_subtasks for subtask_id in submitted_ids):
                    raise InvalidSubtaskError("Subtask does not belong to this task")

            task.title = title
            task.description = description
            task.priority = priority
            task.due_date = due_date
            task.due_time = due_time
            task.due_timezone = due_timezone

            if subtasks is not None:
                submitted_ids_set = set(submitted_ids)

                for subtask_id, existing in existing_subtasks.items():
                    if subtask_id not in submitted_ids_set:
                        await self.db.delete(existing)

                for sort_order, subtask in enumerate(subtasks):
                    if subtask.id is None:
                        self.db.add(
                            Subtask(
                                task_id=task.id,
                                title=subtask.title,
                                completed=False,
                                sort_order=sort_order,
                            )
                        )
                    else:
                        existing = existing_subtasks[subtask.id]
                        existing.title = subtask.title
                        existing.sort_order = sort_order

            if calendar_details_changed:
                sync_service = CalendarSyncService(self.db)

                if task.due_date is not None:
                    await sync_service.enqueue_upsert(
                        employee_id=employee_id,
                        source_type="task",
                        source_id=task.id,
                    )
                else:
                    await sync_service.enqueue_delete(
                        employee_id=employee_id,
                        source_type="task",
                        source_id=task.id,
                    )

            await self.db.commit()
            await self.db.refresh(task)

            return task

        except Exception:
            await self.db.rollback()
            raise

    async def archive_task(
        self,
        employee_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> Task:
        try:
            task = await self.db.scalar(
                select(Task)
                .where(
                    Task.id == task_id,
                    Task.employee_id == employee_id,
                    Task.deleted_at.is_(None),
                )
                .with_for_update()
            )

            if task is None:
                raise TaskNotFoundError("Task not found")

            if task.archived_at is None:
                task.archived_at = datetime.now(timezone.utc)

                await CalendarSyncService(self.db).enqueue_delete(
                    employee_id=employee_id,
                    source_type="task",
                    source_id=task.id,
                )

                await self.db.commit()
                await self.db.refresh(task)

            return task

        except Exception:
            await self.db.rollback()
            raise

    async def restore_task(
        self,
        employee_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> Task:
        try:
            task = await self.db.scalar(
                select(Task)
                .where(
                    Task.id == task_id,
                    Task.employee_id == employee_id,
                    Task.deleted_at.is_(None),
                    Task.archived_at.is_not(None),
                )
                .with_for_update()
            )

            if task is None:
                raise TaskNotFoundError("Archived task not found")

            task.archived_at = None

            if task.due_date is not None:
                await CalendarSyncService(self.db).enqueue_upsert(
                    employee_id=employee_id,
                    source_type="task",
                    source_id=task.id,
                )

            await self.db.commit()
            await self.db.refresh(task)

            return task

        except Exception:
            await self.db.rollback()
            raise

    async def delete_task(
        self,
        employee_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> None:
        try:
            task = await self.db.scalar(
                select(Task)
                .where(
                    Task.id == task_id,
                    Task.employee_id == employee_id,
                    Task.deleted_at.is_(None),
                )
                .with_for_update()
            )

            if task is None:
                raise TaskNotFoundError("Task not found")

            task.deleted_at = datetime.now(timezone.utc)

            await CalendarSyncService(self.db).enqueue_delete(
                employee_id=employee_id,
                source_type="task",
                source_id=task.id,
            )

            await self.db.commit()

        except Exception:
            await self.db.rollback()
            raise

    async def update_subtask_completion(
        self,
        employee_id: uuid.UUID,
        task_id: uuid.UUID,
        subtask_id: uuid.UUID,
        completed: bool,
    ) -> Subtask:
        try:
            subtask = await self.db.scalar(
                select(Subtask)
                .join(
                    Task,
                    Task.id == Subtask.task_id,
                )
                .where(
                    Subtask.id == subtask_id,
                    Subtask.task_id == task_id,
                    Task.employee_id == employee_id,
                    Task.archived_at.is_(None),
                    Task.deleted_at.is_(None),
                )
                .with_for_update(of=Subtask)
            )

            if subtask is None:
                raise SubtaskNotFoundError("Subtask not found")

            if subtask.completed != completed:
                subtask.completed = completed

                await self.db.commit()
                await self.db.refresh(subtask)

            return subtask

        except Exception:
            await self.db.rollback()
            raise
