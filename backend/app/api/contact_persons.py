import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.csrf import validate_request_origin
from app.core.database import get_db
from app.core.pagination import paginate
from app.core.permissions import require_admin
from app.models.contact_person import ContactPerson
from app.schemas.contact_person import (
    ContactPersonResponse,
    CreateContactPersonRequest,
    UpdateContactPersonRequest,
    ContactPersonsPageResponse,
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
    response_model=ContactPersonsPageResponse,
)
async def list_contact_persons(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=100)] = None,
    include_inactive: bool = False,
) -> ContactPersonsPageResponse:
    query = select(ContactPerson)

    if not include_inactive:
        query = query.where(
            ContactPerson.is_active.is_(True),
        )

    if search and search.strip():
        pattern = f"%{search.strip()}%"

        query = query.where(
            or_(
                ContactPerson.name.ilike(pattern),
                ContactPerson.email.ilike(pattern),
                ContactPerson.responsibility.ilike(pattern),
                ContactPerson.department.ilike(pattern),
                ContactPerson.job_title.ilike(pattern),
            )
        )

    query = query.order_by(
        ContactPerson.responsibility.asc(),
        ContactPerson.name.asc(),
        ContactPerson.id.asc(),
    )

    return await paginate(
        db,
        query,
        page=page,
        page_size=page_size,
        response_model=ContactPersonResponse,
    )


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
