import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.capabilities.text_generation import TextGenerationError
from app.ai.capabilities.types import AICapability
from app.ai.registry import (
    AIProviderRegistry,
    ProviderNotConfiguredError,
)
from app.api.assistant_dependencies import (
    get_ai_provider_registry,
    get_orchestrated_assistant,
    get_task_extraction_service,
)
from app.core.auth import get_current_employee
from app.core.csrf import validate_request_origin
from app.core.database import get_db, get_session_factory
from app.models.employee import Employee
from app.schemas.conversation import (
    ConversationDetailResponse,
    ConversationMessageResponse,
    ConversationResponse,
    CreateConversationRequest,
    SendConversationMessageRequest,
    UpdateConversationRequest,
)
from app.schemas.task_extraction import (
    ConversationTaskExtractionRequest,
    ResolvedTaskExtractionResponse,
    TaskExtractionResponse,
)
from app.services.assistant_orchestrator import (
    CapabilityClassificationError,
    CapabilityDisabledError,
)
from app.services.calendar.calendar_extraction import CalendarExtractionError
from app.services.conversation import ConversationService, TaskSourceAmbiguityError
from app.services.orchestrated_assistant import OrchestratedAssistantService
from app.services.task_extraction import TaskExtractionError, TaskExtractionService
from app.services.task_source_resolver import TaskSourceResolutionError, TaskSourceResolver

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


def get_conversation_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    session_factory: Annotated[
        async_sessionmaker[AsyncSession],
        Depends(get_session_factory),
    ],
) -> ConversationService:
    return ConversationService(
        db=db,
        session_factory=session_factory,
    )


def get_messaging_conversation_service(
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
    registry: Annotated[
        AIProviderRegistry,
        Depends(get_ai_provider_registry),
    ],
) -> ConversationService:
    try:
        service.title_provider = registry.get_text_generation(
            AICapability.CONVERSATION_TITLE,
        )

    except ProviderNotConfiguredError:
        service.title_provider = None

    return service


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
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
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
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
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
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
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


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def rename_conversation(
    conversation_id: uuid.UUID,
    payload: UpdateConversationRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> ConversationResponse:
    conversation = await service.rename(
        employee_id=employee.user_id,
        conversation_id=conversation_id,
        title=payload.title,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return ConversationResponse.model_validate(
        conversation,
        from_attributes=True,
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(validate_request_origin)],
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
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
    service: Annotated[
        ConversationService,
        Depends(get_messaging_conversation_service),
    ],
    assistant: Annotated[
        OrchestratedAssistantService,
        Depends(get_orchestrated_assistant),
    ],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> list[ConversationMessageResponse]:
    content = payload.content.strip()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Message cannot be empty",
        )

    try:
        result = await service.send_message(
            employee_id=employee.user_id,
            conversation_id=conversation_id,
            content=content,
            assistant=assistant,
            timezone=payload.timezone,
        )

    except CapabilityDisabledError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This assistant capability is currently unavailable.",
        ) from error

    except CapabilityClassificationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NeuroLens couldn't process your message. Please try again.",
        ) from error

    except TaskSourceAmbiguityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "I couldn't determine which earlier message "
                "you meant. Please specify the assignment "
                "or select the message directly."
            ),
        ) from error

    except (TaskSourceResolutionError, TaskExtractionError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("NeuroLens couldn't prepare task suggestions. Please try again."),
        ) from error

    except CalendarExtractionError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("NeuroLens couldn't prepare calendar suggestions. Please try again."),
        ) from error

    except (TextGenerationError, ProviderNotConfiguredError) as error:
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


@router.post(
    "/{conversation_id}/messages/{message_id}/extract-tasks",
    response_model=TaskExtractionResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def extract_conversation_message_tasks(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
    extraction_service: Annotated[
        TaskExtractionService,
        Depends(get_task_extraction_service),
    ],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> TaskExtractionResponse:
    messages = await service.get_messages(
        employee_id=employee.user_id,
        conversation_id=conversation_id,
    )

    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    source_message = next(
        (message for message in messages if message.id == message_id and message.role == "user"),
        None,
    )

    if source_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source message not found",
        )

    try:
        result = await extraction_service.extract(
            text=source_message.content,
        )

    except ProviderNotConfiguredError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task extraction is currently unavailable",
        ) from error

    except (TextGenerationError, TaskExtractionError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("NeuroLens couldn't extract tasks from this message. Please try again."),
        ) from error

    return TaskExtractionResponse(
        tasks=result.tasks,
    )


@router.post(
    "/{conversation_id}/extract-tasks",
    response_model=ResolvedTaskExtractionResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def extract_conversation_tasks(
    conversation_id: uuid.UUID,
    payload: ConversationTaskExtractionRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
    registry: Annotated[
        AIProviderRegistry,
        Depends(get_ai_provider_registry),
    ],
    extraction_service: Annotated[
        TaskExtractionService,
        Depends(get_task_extraction_service),
    ],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> ResolvedTaskExtractionResponse:
    messages = await service.get_messages(
        employee_id=employee.user_id,
        conversation_id=conversation_id,
    )

    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    candidates = [
        message for message in messages if message.role == "user" and message.content.strip()
    ]

    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No previous employee messages are available for task extraction.",
        )

    resolver = TaskSourceResolver(
        registry=registry,
    )

    try:
        source_message_id = await resolver.resolve(
            request=payload.request,
            messages=candidates,
        )

    except ProviderNotConfiguredError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task source resolution is currently unavailable",
        ) from error

    except (TextGenerationError, TaskSourceResolutionError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("NeuroLens couldn't identify the source message. Please try again."),
        ) from error

    if source_message_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "I couldn't determine which earlier message you meant. "
                "Please specify the request or select the message directly."
            ),
        )

    # The resolver's output must correspond to a user-authored
    # message in this employee-owned conversation.
    source_message = next(
        (message for message in candidates if message.id == source_message_id),
        None,
    )

    if source_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source message not found",
        )

    try:
        result = await extraction_service.extract(
            text=source_message.content,
        )

    except ProviderNotConfiguredError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task extraction is currently unavailable",
        ) from error

    except (TextGenerationError, TaskExtractionError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("NeuroLens couldn't extract tasks from this message. Please try again."),
        ) from error

    return ResolvedTaskExtractionResponse(
        source_message_id=source_message.id,
        tasks=result.tasks,
    )
