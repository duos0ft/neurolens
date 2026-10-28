import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.contact_person import ContactPerson
from app.services.contact_person import ContactPersonService


@pytest.fixture
async def contact_cleanup(
    test_admin_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[list[uuid.UUID]]:
    contact_ids: list[uuid.UUID] = []

    try:
        yield contact_ids

    finally:
        if contact_ids:
            async with test_admin_session_factory() as db:
                await db.execute(
                    delete(ContactPerson).where(
                        ContactPerson.id.in_(contact_ids),
                    )
                )

                await db.commit()


@pytest.mark.asyncio
async def test_can_create_contact_person(
    test_session_factory: async_sessionmaker[AsyncSession],
    contact_cleanup: list[uuid.UUID],
) -> None:
    email = f"contact-{uuid.uuid4().hex}@example.com"

    async with test_session_factory() as db:
        service = ContactPersonService(db)

        contact = await service.create(
            name="  Sarah   Williams  ",
            email=email,
            responsibility="  General   HR  ",
            job_title="HR Manager",
            department="Human Resources",
        )

        contact_cleanup.append(contact.id)

        assert contact.id is not None
        assert contact.name == "Sarah Williams"
        assert contact.email == email
        assert contact.responsibility == "General HR"
        assert contact.job_title == "HR Manager"
        assert contact.department == "Human Resources"
        assert contact.is_active is True
        assert contact.is_primary is False

        stored = await db.get(ContactPerson, contact.id)

        assert stored is not None
        assert stored.email == email


@pytest.mark.asyncio
async def test_can_list_active_contact_persons(
    test_session_factory: async_sessionmaker[AsyncSession],
    contact_cleanup: list[uuid.UUID],
) -> None:
    async with test_session_factory() as db:
        service = ContactPersonService(db)

        active = await service.create(
            name="Active Contact",
            email=f"active-{uuid.uuid4().hex}@example.com",
            responsibility="Test HR",
        )

        contact_cleanup.append(active.id)

        inactive = await service.create(
            name="Inactive Contact",
            email=f"inactive-{uuid.uuid4().hex}@example.com",
            responsibility="Test IT",
        )

        contact_cleanup.append(inactive.id)

        deactivated = await service.deactivate(inactive.id)

        assert deactivated is not None
        assert deactivated.is_active is False

        contacts = await service.list()
        contact_ids = {contact.id for contact in contacts}

        assert active.id in contact_ids
        assert inactive.id not in contact_ids

        all_contacts = await service.list(include_inactive=True)
        all_ids = {contact.id for contact in all_contacts}

        assert active.id in all_ids
        assert inactive.id in all_ids


@pytest.mark.asyncio
async def test_can_update_contact_person(
    test_session_factory: async_sessionmaker[AsyncSession],
    contact_cleanup: list[uuid.UUID],
) -> None:
    async with test_session_factory() as db:
        service = ContactPersonService(db)

        contact = await service.create(
            name="Sarah Williams",
            email=f"sarah-{uuid.uuid4().hex}@example.com",
            responsibility="General HR",
        )

        contact_cleanup.append(contact.id)
        contact_id = contact.id
        email = contact.email

        updated = await service.update(
            contact_id=contact_id,
            name="Sarah Johnson",
            email=email,
            responsibility="Payroll",
            job_title="Payroll Manager",
            department="Finance",
            is_primary=False,
            is_active=True,
        )

        assert updated is not None
        assert updated.name == "Sarah Johnson"
        assert updated.responsibility == "Payroll"
        assert updated.job_title == "Payroll Manager"
        assert updated.department == "Finance"

        await db.refresh(updated)

        assert updated.name == "Sarah Johnson"


@pytest.mark.asyncio
async def test_can_assign_primary_contact(
    test_session_factory: async_sessionmaker[AsyncSession],
    contact_cleanup: list[uuid.UUID],
) -> None:
    responsibility = f"HR-{uuid.uuid4().hex}"

    async with test_session_factory() as db:
        service = ContactPersonService(db)

        contact = await service.create(
            name="Primary Contact",
            email=f"primary-{uuid.uuid4().hex}@example.com",
            responsibility=responsibility,
            is_primary=True,
        )

        contact_cleanup.append(contact.id)

        assert contact.is_primary is True

        stored = await service.get(contact.id)

        assert stored is not None
        assert stored.is_active is True
        assert stored.is_primary is True


@pytest.mark.asyncio
async def test_assigning_new_primary_replaces_existing_primary(
    test_session_factory: async_sessionmaker[AsyncSession],
    contact_cleanup: list[uuid.UUID],
) -> None:
    responsibility = f"General-HR-{uuid.uuid4().hex}"

    async with test_session_factory() as db:
        service = ContactPersonService(db)

        first = await service.create(
            name="First HR Contact",
            email=f"first-{uuid.uuid4().hex}@example.com",
            responsibility=responsibility,
            is_primary=True,
        )

        contact_cleanup.append(first.id)
        first_id = first.id

        second = await service.create(
            name="Second HR Contact",
            email=f"second-{uuid.uuid4().hex}@example.com",
            responsibility=responsibility,
            is_primary=True,
        )

        contact_cleanup.append(second.id)
        second_id = second.id

        await db.refresh(first)
        await db.refresh(second)

        assert first.is_primary is False
        assert second.is_primary is True

        result = await db.scalars(
            select(ContactPerson).where(
                ContactPerson.responsibility == responsibility,
                ContactPerson.is_primary.is_(True),
                ContactPerson.is_active.is_(True),
            )
        )

        primary_contacts = list(result.all())

        assert len(primary_contacts) == 1
        assert primary_contacts[0].id == second_id
        assert first_id != second_id


@pytest.mark.asyncio
async def test_updating_contact_can_assign_new_primary(
    test_session_factory: async_sessionmaker[AsyncSession],
    contact_cleanup: list[uuid.UUID],
) -> None:
    responsibility = f"HR-{uuid.uuid4().hex}"

    async with test_session_factory() as db:
        service = ContactPersonService(db)

        first = await service.create(
            name="First Contact",
            email=f"first-{uuid.uuid4().hex}@example.com",
            responsibility=responsibility,
            is_primary=True,
        )

        contact_cleanup.append(first.id)

        second = await service.create(
            name="Second Contact",
            email=f"second-{uuid.uuid4().hex}@example.com",
            responsibility=responsibility,
        )

        contact_cleanup.append(second.id)

        updated = await service.update(
            contact_id=second.id,
            name=second.name,
            email=second.email,
            responsibility=responsibility,
            job_title=None,
            department=None,
            is_primary=True,
            is_active=True,
        )

        assert updated is not None

        await db.refresh(first)
        await db.refresh(second)

        assert first.is_primary is False
        assert second.is_primary is True


@pytest.mark.asyncio
async def test_changing_primary_contact_responsibility(
    test_session_factory: async_sessionmaker[AsyncSession],
    contact_cleanup: list[uuid.UUID],
) -> None:
    original_responsibility = f"HR-{uuid.uuid4().hex}"
    new_responsibility = f"Payroll-{uuid.uuid4().hex}"

    async with test_session_factory() as db:
        service = ContactPersonService(db)

        contact = await service.create(
            name="HR Contact",
            email=f"hr-{uuid.uuid4().hex}@example.com",
            responsibility=original_responsibility,
            is_primary=True,
        )

        contact_cleanup.append(contact.id)

        updated = await service.update(
            contact_id=contact.id,
            name=contact.name,
            email=contact.email,
            responsibility=new_responsibility,
            job_title="Payroll Manager",
            department="Finance",
            is_primary=True,
            is_active=True,
        )

        assert updated is not None
        assert updated.responsibility == new_responsibility
        assert updated.is_primary is True

        await db.refresh(contact)

        assert contact.responsibility == new_responsibility
        assert contact.is_primary is True


@pytest.mark.asyncio
async def test_deactivating_primary_contact_removes_primary_status(
    test_session_factory: async_sessionmaker[AsyncSession],
    contact_cleanup: list[uuid.UUID],
) -> None:
    async with test_session_factory() as db:
        service = ContactPersonService(db)

        contact = await service.create(
            name="Primary HR Contact",
            email=f"hr-{uuid.uuid4().hex}@example.com",
            responsibility=f"HR-{uuid.uuid4().hex}",
            is_primary=True,
        )

        contact_cleanup.append(contact.id)

        deactivated = await service.deactivate(contact.id)

        assert deactivated is not None
        assert deactivated.is_active is False
        assert deactivated.is_primary is False

        await db.refresh(contact)

        assert contact.is_active is False
        assert contact.is_primary is False


@pytest.mark.asyncio
async def test_reactivating_contact_does_not_automatically_become_primary(
    test_session_factory: async_sessionmaker[AsyncSession],
    contact_cleanup: list[uuid.UUID],
) -> None:
    async with test_session_factory() as db:
        service = ContactPersonService(db)

        contact = await service.create(
            name="Inactive HR Contact",
            email=f"reactivate-{uuid.uuid4().hex}@example.com",
            responsibility=f"HR-{uuid.uuid4().hex}",
            is_primary=True,
        )

        contact_cleanup.append(contact.id)

        await service.deactivate(contact.id)

        reactivated = await service.update(
            contact_id=contact.id,
            name=contact.name,
            email=contact.email,
            responsibility=contact.responsibility,
            job_title=None,
            department=None,
            is_primary=False,
            is_active=True,
        )

        assert reactivated is not None
        assert reactivated.is_active is True
        assert reactivated.is_primary is False


@pytest.mark.asyncio
async def test_duplicate_contact_email_is_rejected(
    test_session_factory: async_sessionmaker[AsyncSession],
    contact_cleanup: list[uuid.UUID],
) -> None:
    email = f"duplicate-{uuid.uuid4().hex}@example.com"

    async with test_session_factory() as db:
        service = ContactPersonService(db)

        first = await service.create(
            name="First Contact",
            email=email,
            responsibility="HR",
        )

        first_id = first.id
        contact_cleanup.append(first_id)

        with pytest.raises(IntegrityError):
            await service.create(
                name="Second Contact",
                email=email,
                responsibility="IT",
            )

        await db.rollback()

        stored = await service.get(first_id)

        assert stored is not None
        assert stored.email == email
        assert stored.name == "First Contact"


@pytest.mark.asyncio
async def test_unknown_contact_returns_none(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as db:
        service = ContactPersonService(db)

        unknown_id = uuid.uuid4()

        assert await service.get(unknown_id) is None
        assert await service.deactivate(unknown_id) is None


@pytest.mark.asyncio
async def test_primary_contact_must_be_unique_per_responsibility(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_admin_session_factory: async_sessionmaker[AsyncSession],
    contact_cleanup: list[uuid.UUID],
) -> None:
    responsibility = f"HR-{uuid.uuid4().hex}"

    async with test_session_factory() as db:
        service = ContactPersonService(db)

        first = await service.create(
            name="First Primary",
            email=f"primary1-{uuid.uuid4().hex}@example.com",
            responsibility=responsibility,
            is_primary=True,
        )

        contact_cleanup.append(first.id)

    second_id = uuid.uuid4()

    try:
        async with test_admin_session_factory() as db:
            db.add(
                ContactPerson(
                    id=second_id,
                    name="Duplicate Primary",
                    email=f"primary2-{uuid.uuid4().hex}@example.com",
                    responsibility=responsibility,
                    is_primary=True,
                    is_active=True,
                )
            )

            with pytest.raises(IntegrityError):
                await db.commit()

            await db.rollback()

    finally:
        contact_cleanup.append(second_id)
