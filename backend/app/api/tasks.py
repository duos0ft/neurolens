from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.conversations import validate_mutation_csrf
from app.core.auth import get_current_employee
from app.core.database import get_db
from app.models.employee import Employee
from app.models.subtask import Subtask
from app.models.task import Task
from app.schemas.task import (
    SaveTaskSuggestionsRequest,
    TaskResponse,
    SubtaskResponse,
    SaveReviewedTasksRequest,
)
from app.services.task import (
    InvalidTaskSelectionError,
    TaskService,
    TaskSuggestionNotFoundError,
)


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


def get_task_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskService:
    return TaskService(db=db)


async def build_task_responses(
    db: AsyncSession,
    tasks: list[Task],
) -> list[TaskResponse]:
    if not tasks:
        return []

    task_ids = [task.id for task in tasks]

    result = await db.scalars(
        select(Subtask)
        .where(Subtask.task_id.in_(task_ids))
        .order_by(Subtask.task_id, Subtask.sort_order)
    )

    subtasks_by_task = {task_id: [] for task_id in task_ids}

    for subtask in result.all():
        subtasks_by_task[subtask.task_id].append(SubtaskResponse.model_validate(subtask))

    return [
        TaskResponse(
            id=task.id,
            employee_id=task.employee_id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            source_message_id=task.source_message_id,
            source_suggestion_index=task.source_suggestion_index,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            subtasks=subtasks_by_task[task.id],
        )
        for task in tasks
    ]


@router.post(
    "/from-suggestions",
    response_model=list[TaskResponse],
    status_code=status.HTTP_200_OK,
)
async def save_task_suggestions(
    payload: SaveTaskSuggestionsRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[TaskService, Depends(get_task_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> list[TaskResponse]:
    try:
        saved_tasks = await service.save_suggestions(
            employee_id=employee.user_id,
            message_id=payload.message_id,
            selected_indices=payload.selected_indices,
        )

    except TaskSuggestionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task suggestions not found",
        ) from error

    except InvalidTaskSelectionError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return await build_task_responses(db=db, tasks=saved_tasks)


@router.post(
    "/from-reviewed-suggestions",
    response_model=list[TaskResponse],
    status_code=status.HTTP_200_OK,
)
async def save_reviewed_task_suggestions(
    payload: SaveReviewedTasksRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[TaskService, Depends(get_task_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> list[TaskResponse]:
    try:
        saved_tasks = await service.save_reviewed_suggestions(
            employee_id=employee.user_id,
            message_id=payload.message_id,
            reviewed_tasks=payload.tasks,
        )

    except TaskSuggestionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task suggestions not found",
        ) from error

    except InvalidTaskSelectionError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return await build_task_responses(
        db=db,
        tasks=saved_tasks,
    )
