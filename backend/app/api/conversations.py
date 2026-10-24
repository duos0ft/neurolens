import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.capabilities.text_generation import TextGenerationError
from app.api.assistant import get_assistant_service
from app.core.auth import get_current_employee
from app.core.csrf import validate_request_origin
from app.core.database import get_db
from app.models.employee import Employee
from app.schemas.conversation import (
    ConversationDetailResponse,
    ConversationMessageResponse,
    ConversationResponse,
    CreateConversationRequest,
    SendConversationMessageRequest,
)
from app.services.assistant import AssistantService
from app.services.conversation import ConversationService


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


def get_conversation_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationService:
    return ConversationService(db)


async def validate_mutation_csrf(
    request: Request,
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> None:
    try:
        await csrf_protect.validate_csrf(request)

    except CsrfProtectError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from error


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(validate_request_origin)],
)
async def create_conversation(
    payload: CreateConversationRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> ConversationResponse:
    conversation = await service.create(
        employee_id=employee.user_id,
        title=payload.title,
    )

    return ConversationResponse.model_validate(
        conversation,
        from_attributes=True,
    )


@router.get(
    "",
    response_model=list[ConversationResponse],
)
async def list_conversations(
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> list[ConversationResponse]:
    conversations = await service.list(employee.user_id)

    return [
        ConversationResponse.model_validate(
            conversation,
            from_attributes=True,
        )
        for conversation in conversations
    ]


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
)
async def get_conversation(
    conversation_id: uuid.UUID,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ConversationDetailResponse:
    conversation = await service.get(
        employee_id=employee.user_id,
        conversation_id=conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = await service.get_messages(
        employee_id=employee.user_id,
        conversation_id=conversation_id,
    )

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            ConversationMessageResponse.model_validate(
                message,
                from_attributes=True,
            )
            for message in (messages or [])
        ],
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(validate_request_origin)],
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> None:
    deleted = await service.delete(
        employee_id=employee.user_id,
        conversation_id=conversation_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )


@router.post(
    "/{conversation_id}/messages",
    response_model=list[ConversationMessageResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(validate_request_origin)],
)
async def send_conversation_message(
    conversation_id: uuid.UUID,
    payload: SendConversationMessageRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    assistant: Annotated[AssistantService, Depends(get_assistant_service)],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> list[ConversationMessageResponse]:
    if not payload.content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Message cannot be empty",
        )

    try:
        result = await service.send_message(
            employee_id=employee.user_id,
            conversation_id=conversation_id,
            content=payload.content,
            assistant=assistant,
        )

    except TextGenerationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI assistant is temporarily unavailable",
        ) from error

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return [
        ConversationMessageResponse.model_validate(
            message,
            from_attributes=True,
        )
        for message in result
    ]
