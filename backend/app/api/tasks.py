import uuid
from math import ceil
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.conversations import validate_mutation_csrf
from app.core.auth import get_current_employee
from app.core.database import get_db
from app.models.employee import Employee
from app.models.subtask import Subtask
from app.models.task import Task
from app.schemas.pagination import PageResponse
from app.schemas.task import (
    SaveTaskSuggestionsRequest,
    TaskResponse,
    SubtaskResponse,
    SaveReviewedTasksRequest,
    TaskStatsResponse,
    UpdateTaskStatusRequest,
    UpdateTaskRequest,
    CreateTaskRequest,
    UpdateSubtaskCompletionRequest,
)
from app.services.task import (
    InvalidTaskSelectionError,
    TaskService,
    TaskSuggestionNotFoundError,
    TaskNotFoundError,
    SubtaskNotFoundError,
    InvalidSubtaskError,
)


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


class SavedSuggestionResponse(BaseModel):
    suggestion_index: int
    task_id: uuid.UUID
    archived: bool
    deleted: bool


class SavedSuggestionsResponse(BaseModel):
    saved: list[SavedSuggestionResponse]


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
            archived_at=task.archived_at,
            deleted_at=task.deleted_at,
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


@router.get(
    "/saved-suggestions",
    response_model=SavedSuggestionsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_saved_task_suggestions(
    message_id: Annotated[uuid.UUID, Query()],
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> SavedSuggestionsResponse:
    try:
        saved_suggestions = await service.get_saved_suggestions(
            employee_id=employee.user_id,
            message_id=message_id,
        )

    except TaskSuggestionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task suggestions not found",
        ) from error

    return SavedSuggestionsResponse(
        saved=[
            SavedSuggestionResponse(
                suggestion_index=suggestion_index,
                task_id=task_id,
                archived=archived,
                deleted=deleted,
            )
            for suggestion_index, task_id, archived, deleted in saved_suggestions
        ],
    )


@router.get(
    "",
    response_model=PageResponse[TaskResponse],
    status_code=status.HTTP_200_OK,
)
async def list_tasks(
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[TaskService, Depends(get_task_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    task_status: Annotated[
        Literal["todo", "in_progress", "completed"] | None,
        Query(alias="status"),
    ] = None,
    priority: Annotated[
        Literal["low", "medium", "high"] | None,
        Query(),
    ] = None,
    sort_by: Annotated[
        Literal["created_at", "updated_at", "due_date", "priority"],
        Query(),
    ] = "created_at",
    sort_order: Annotated[
        Literal["asc", "desc"],
        Query(),
    ] = "desc",
    archived: Annotated[bool, Query()] = False,
) -> PageResponse[TaskResponse]:
    tasks, total_items = await service.get_tasks(
        employee_id=employee.user_id,
        page=page,
        page_size=page_size,
        status=task_status,
        priority=priority,
        sort_by=sort_by,
        sort_order=sort_order,
        archived=archived,
    )

    return PageResponse[TaskResponse](
        items=await build_task_responses(
            db=db,
            tasks=tasks,
        ),
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=ceil(total_items / page_size),
    )


@router.get(
    "/stats",
    response_model=TaskStatsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_task_stats(
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskStatsResponse:
    counts = await service.get_task_stats(
        employee_id=employee.user_id,
    )

    return TaskStatsResponse(**counts)


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def update_task_status(
    task_id: uuid.UUID,
    payload: UpdateTaskStatusRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[TaskService, Depends(get_task_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> TaskResponse:
    try:
        task = await service.update_status(
            employee_id=employee.user_id,
            task_id=task_id,
            status=payload.status,
        )

    except TaskNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from error

    responses = await build_task_responses(
        db=db,
        tasks=[task],
    )

    return responses[0]


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    payload: CreateTaskRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[TaskService, Depends(get_task_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> TaskResponse:
    task = await service.create_task(
        employee_id=employee.user_id,
        title=payload.title.strip(),
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date,
        subtasks=payload.subtasks,
    )

    responses = await build_task_responses(
        db=db,
        tasks=[task],
    )

    return responses[0]


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def update_task(
    task_id: uuid.UUID,
    payload: UpdateTaskRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[TaskService, Depends(get_task_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> TaskResponse:
    try:
        task = await service.update_task(
            employee_id=employee.user_id,
            task_id=task_id,
            title=payload.title.strip(),
            description=payload.description,
            priority=payload.priority,
            due_date=payload.due_date,
            subtasks=payload.subtasks,
        )

    except TaskNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from error

    except InvalidSubtaskError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    responses = await build_task_responses(
        db=db,
        tasks=[task],
    )

    return responses[0]


@router.patch(
    "/{task_id}/archive",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def archive_task(
    task_id: uuid.UUID,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[TaskService, Depends(get_task_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> TaskResponse:
    try:
        task = await service.archive_task(
            employee_id=employee.user_id,
            task_id=task_id,
        )

    except TaskNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from error

    responses = await build_task_responses(
        db=db,
        tasks=[task],
    )

    return responses[0]


@router.patch(
    "/{task_id}/restore",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def restore_task(
    task_id: uuid.UUID,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[TaskService, Depends(get_task_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> TaskResponse:
    try:
        task = await service.restore_task(
            employee_id=employee.user_id,
            task_id=task_id,
        )

    except TaskNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archived task not found",
        ) from error

    responses = await build_task_responses(
        db=db,
        tasks=[task],
    )

    return responses[0]


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    task_id: uuid.UUID,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[TaskService, Depends(get_task_service)],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> None:
    try:
        await service.delete_task(
            employee_id=employee.user_id,
            task_id=task_id,
        )

    except TaskNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from error


@router.patch(
    "/{task_id}/subtasks/{subtask_id}/completion",
    response_model=SubtaskResponse,
    status_code=status.HTTP_200_OK,
)
async def update_subtask_completion(
    task_id: uuid.UUID,
    subtask_id: uuid.UUID,
    payload: UpdateSubtaskCompletionRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[TaskService, Depends(get_task_service)],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> SubtaskResponse:
    try:
        subtask = await service.update_subtask_completion(
            employee_id=employee.user_id,
            task_id=task_id,
            subtask_id=subtask_id,
            completed=payload.completed,
        )

    except SubtaskNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subtask not found",
        ) from error

    return SubtaskResponse.model_validate(subtask)
