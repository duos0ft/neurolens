from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError

from app.ai.capabilities.text_generation import (
    TextGenerationError,
    TextGenerationProvider,
)
from app.ai.registry import ProviderNotConfiguredError
from app.ai.resolver import resolve_text_generation_provider
from app.api.assistant_dependencies import get_orchestrated_assistant
from app.core.auth import get_current_employee
from app.core.csrf import validate_request_origin
from app.models.employee import Employee
from app.schemas.assistant import (
    AssistantMessageRequest,
    AssistantMessageResponse,
)
from app.services.assistant import AssistantService
from app.services.orchestrated_assistant import OrchestratedAssistantService


router = APIRouter(
    prefix="/assistant",
    tags=["Assistant"],
)


# Retained for legacy callers and tests during migration.
def get_assistant_service() -> AssistantService:
    provider: TextGenerationProvider = resolve_text_generation_provider()

    return AssistantService(provider=provider)


@router.post(
    "/messages",
    response_model=AssistantMessageResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def send_message(
    request: Request,
    payload: AssistantMessageRequest,
    employee: Annotated[Employee, Depends(get_current_employee)],
    assistant: Annotated[
        OrchestratedAssistantService,
        Depends(get_orchestrated_assistant),
    ],
    csrf_protect: Annotated[CsrfProtect, Depends()],
) -> AssistantMessageResponse:
    try:
        await csrf_protect.validate_csrf(request)

    except CsrfProtectError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        ) from error

    message = payload.message.strip()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Message cannot be empty",
        )

    try:
        response = await assistant.respond(
            message=message,
        )

    except (TextGenerationError, ProviderNotConfiguredError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI assistant is temporarily unavailable",
        ) from error

    return AssistantMessageResponse(
        content=response.content,
        model=response.model,
    )
