import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.csrf import validate_request_origin
from app.core.database import get_db
from app.core.permissions import require_admin
from app.schemas.contact_person import (
    ContactPersonResponse,
    CreateContactPersonRequest,
    UpdateContactPersonRequest,
)
from app.services.contact_person import ContactPersonService

router = APIRouter(
    prefix="/admin/contact-persons",
    tags=["Contact Persons"],
    dependencies=[Depends(require_admin)],
)


def get_contact_person_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ContactPersonService:
    return ContactPersonService(db)


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


@router.get(
    "",
    response_model=list[ContactPersonResponse],
)
async def list_contact_persons(
    service: Annotated[
        ContactPersonService,
        Depends(get_contact_person_service),
    ],
    include_inactive: bool = False,
) -> list[ContactPersonResponse]:
    contacts = await service.list(
        include_inactive=include_inactive,
    )

    return [ContactPersonResponse.model_validate(contact) for contact in contacts]


@router.post(
    "",
    response_model=ContactPersonResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(validate_request_origin)],
)
async def create_contact_person(
    payload: CreateContactPersonRequest,
    service: Annotated[
        ContactPersonService,
        Depends(get_contact_person_service),
    ],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> ContactPersonResponse:
    try:
        contact = await service.create(
            name=payload.name,
            email=payload.email,
            responsibility=payload.responsibility,
            job_title=payload.job_title,
            department=payload.department,
            is_primary=payload.is_primary,
        )

    except IntegrityError as error:
        await service.db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact information conflicts with an existing record",
        ) from error

    return ContactPersonResponse.model_validate(contact)


@router.patch(
    "/{contact_id}",
    response_model=ContactPersonResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def update_contact_person(
    contact_id: uuid.UUID,
    payload: UpdateContactPersonRequest,
    service: Annotated[
        ContactPersonService,
        Depends(get_contact_person_service),
    ],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> ContactPersonResponse:
    try:
        contact = await service.update(
            contact_id=contact_id,
            name=payload.name,
            email=payload.email,
            responsibility=payload.responsibility,
            job_title=payload.job_title,
            department=payload.department,
            is_primary=payload.is_primary,
            is_active=payload.is_active,
        )

    except IntegrityError as error:
        await service.db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact information conflicts with an existing record",
        ) from error

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact person not found",
        )

    return ContactPersonResponse.model_validate(contact)


@router.post(
    "/{contact_id}/deactivate",
    response_model=ContactPersonResponse,
    dependencies=[Depends(validate_request_origin)],
)
async def deactivate_contact_person(
    contact_id: uuid.UUID,
    service: Annotated[
        ContactPersonService,
        Depends(get_contact_person_service),
    ],
    _: Annotated[None, Depends(validate_mutation_csrf)],
) -> ContactPersonResponse:
    contact = await service.deactivate(
        contact_id=contact_id,
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact person not found",
        )

    return ContactPersonResponse.model_validate(contact)
