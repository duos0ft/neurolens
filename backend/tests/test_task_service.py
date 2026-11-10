import uuid
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.conversation_message import ConversationMessage
from app.models.subtask import Subtask
from app.models.task import Task
from app.services.conversation import ConversationService
from app.services.task import (
    InvalidTaskSelectionError,
    TaskService,
    TaskSuggestionNotFoundError,
)


async def create_task_suggestions(
    db: AsyncSession,
    employee_id: uuid.UUID,
) -> tuple[uuid.UUID, uuid.UUID]:
    conversation_service = ConversationService(db=db)

    conversation = await conversation_service.create(
        employee_id=employee_id,
        title="Client feedback",
    )

    user_message = ConversationMessage(
        conversation_id=conversation.id,
        sequence_number=1,
        role="user",
        content=("Review last week's client feedback and prepare a summary for the team."),
    )

    assistant_message = ConversationMessage(
        conversation_id=conversation.id,
        sequence_number=2,
        role="assistant",
        content="I found two possible task suggestions.",
        model="neurolens-task-extraction",
        task_suggestions={
            "version": 1,
            "source_message_id": None,
            "tasks": [
                {
                    "title": "Review client feedback",
                    "description": (
                        "Review last week's client feedback and identify the main issues."
                    ),
                    "priority": "medium",
                    "due_date": None,
                    "source_text": "Review last week's client feedback",
                    "subtasks": [
                        {
                            "title": "Read the client feedback",
                        },
                        {
                            "title": "Identify the main issues",
                        },
                    ],
                },
                {
                    "title": "Prepare the team summary",
                    "description": "Summarize the client feedback for the team.",
                    "priority": "low",
                    "due_date": "2026-11-20",
                    "source_text": "prepare a summary for the team",
                    "subtasks": [],
                },
            ],
        },
    )

    db.add_all(
        [
            user_message,
            assistant_message,
        ]
    )

    await db.commit()
    await db.refresh(assistant_message)

    return conversation.id, assistant_message.id


@pytest.mark.asyncio
async def test_saves_only_selected_suggestions(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    async with test_session_factory() as db:
        _, message_id = await create_task_suggestions(
            db=db,
            employee_id=employee_id,
        )

        service = TaskService(db=db)

        saved = await service.save_suggestions(
            employee_id=employee_id,
            message_id=message_id,
            selected_indices=[1],
        )

        assert len(saved) == 1

        task = saved[0]

        assert task.employee_id == employee_id
        assert task.title == "Prepare the team summary"
        assert task.status == "todo"
        assert task.priority == "low"
        assert task.due_date == date(2026, 11, 20)
        assert task.source_message_id == message_id
        assert task.source_suggestion_index == 1

        stored = list(
            (
                await db.scalars(
                    select(Task).where(
                        Task.employee_id == employee_id,
                        Task.source_message_id == message_id,
                    )
                )
            ).all()
        )

        assert len(stored) == 1
        assert stored[0].id == task.id


@pytest.mark.asyncio
async def test_saves_task_with_subtasks(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    async with test_session_factory() as db:
        _, message_id = await create_task_suggestions(
            db=db,
            employee_id=employee_id,
        )

        service = TaskService(db=db)

        saved = await service.save_suggestions(
            employee_id=employee_id,
            message_id=message_id,
            selected_indices=[0],
        )

        assert len(saved) == 1

        task = saved[0]

        assert task.title == "Review client feedback"
        assert task.priority == "medium"
        assert task.due_date is None

        subtasks = list(
            (
                await db.scalars(
                    select(Subtask).where(Subtask.task_id == task.id).order_by(Subtask.sort_order)
                )
            ).all()
        )

        assert len(subtasks) == 2

        assert [subtask.title for subtask in subtasks] == [
            "Read the client feedback",
            "Identify the main issues",
        ]

        assert [subtask.sort_order for subtask in subtasks] == [
            0,
            1,
        ]

        assert all(subtask.completed is False for subtask in subtasks)


@pytest.mark.asyncio
async def test_repeated_confirmation_does_not_duplicate_tasks(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    async with test_session_factory() as db:
        _, message_id = await create_task_suggestions(
            db=db,
            employee_id=employee_id,
        )

        service = TaskService(db=db)

        first = await service.save_suggestions(
            employee_id=employee_id,
            message_id=message_id,
            selected_indices=[0],
        )

        second = await service.save_suggestions(
            employee_id=employee_id,
            message_id=message_id,
            selected_indices=[0, 1],
        )

        assert len(first) == 1
        assert len(second) == 2

        assert second[0].id == first[0].id

        tasks = list(
            (
                await db.scalars(
                    select(Task).where(
                        Task.employee_id == employee_id,
                        Task.source_message_id == message_id,
                    )
                )
            ).all()
        )

        assert len(tasks) == 2

        subtasks = list(
            (
                await db.scalars(
                    select(Subtask).where(
                        Subtask.task_id == first[0].id,
                    )
                )
            ).all()
        )

        # Repeated confirmation must not duplicate subtasks.
        assert len(subtasks) == 2


@pytest.mark.asyncio
async def test_employee_cannot_save_another_employees_suggestions(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    owner_id = test_invitation.employee_id
    unauthorized_employee_id = uuid.uuid4()

    async with test_session_factory() as db:
        _, message_id = await create_task_suggestions(
            db=db,
            employee_id=owner_id,
        )

        service = TaskService(db=db)

        with pytest.raises(TaskSuggestionNotFoundError):
            await service.save_suggestions(
                employee_id=unauthorized_employee_id,
                message_id=message_id,
                selected_indices=[0],
            )

        stored_tasks = list(
            (
                await db.scalars(
                    select(Task).where(
                        Task.source_message_id == message_id,
                    )
                )
            ).all()
        )

        assert stored_tasks == []


@pytest.mark.asyncio
async def test_invalid_selection_does_not_save_any_tasks(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    async with test_session_factory() as db:
        _, message_id = await create_task_suggestions(
            db=db,
            employee_id=employee_id,
        )

        service = TaskService(db=db)

        with pytest.raises(InvalidTaskSelectionError):
            await service.save_suggestions(
                employee_id=employee_id,
                message_id=message_id,
                selected_indices=[0, 99],
            )

        stored_tasks = list(
            (
                await db.scalars(
                    select(Task).where(
                        Task.source_message_id == message_id,
                    )
                )
            ).all()
        )

        assert stored_tasks == []


@pytest.mark.asyncio
async def test_saved_task_survives_conversation_deletion(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_invitation,
) -> None:
    employee_id = test_invitation.employee_id

    async with test_session_factory() as db:
        conversation_id, message_id = await create_task_suggestions(
            db=db,
            employee_id=employee_id,
        )

        task_service = TaskService(db=db)

        saved = await task_service.save_suggestions(
            employee_id=employee_id,
            message_id=message_id,
            selected_indices=[0],
        )

        task_id = saved[0].id

        conversation_service = ConversationService(db=db)

        deleted = await conversation_service.delete(
            employee_id=employee_id,
            conversation_id=conversation_id,
        )

        assert deleted is True

    # A separate session verifies that the task persists
    # after the conversation and its messages are deleted.
    async with test_session_factory() as db:
        task = await db.get(Task, task_id)

        assert task is not None
        assert task.employee_id == employee_id
        assert task.title == "Review client feedback"

        assert task.source_message_id is None
        assert task.source_suggestion_index == 0

        subtasks = list(
            (
                await db.scalars(
                    select(Subtask)
                    .where(Subtask.task_id == task_id)
                    .order_by(Subtask.sort_order)
                )
            ).all()
        )

        assert len(subtasks) == 2
