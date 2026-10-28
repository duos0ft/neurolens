import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact_person import ContactPerson


class ContactPersonService:
    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def create(
        self,
        name: str,
        email: str,
        responsibility: str,
        job_title: str | None = None,
        department: str | None = None,
        is_primary: bool = False,
    ) -> ContactPerson:
        contact = ContactPerson(
            name=" ".join(name.split()),
            email=email.strip().lower(),
            responsibility=" ".join(responsibility.split()),
            job_title=" ".join(job_title.split()) if job_title else None,
            department=" ".join(department.split()) if department else None,
            is_primary=False,
        )

        self.db.add(contact)
        await self.db.flush()

        if is_primary:
            await self._assign_primary(contact)

        await self.db.commit()
        await self.db.refresh(contact)

        return contact

    async def list(
        self,
        include_inactive: bool = False,
    ) -> list[ContactPerson]:
        query = select(ContactPerson)

        if not include_inactive:
            query = query.where(ContactPerson.is_active.is_(True))

        result = await self.db.scalars(
            query.order_by(
                ContactPerson.responsibility.asc(),
                ContactPerson.name.asc(),
            )
        )

        return list(result.all())

    async def get(
        self,
        contact_id: uuid.UUID,
    ) -> ContactPerson | None:
        return await self.db.get(ContactPerson, contact_id)

    async def update(
        self,
        contact_id: uuid.UUID,
        name: str,
        email: str,
        responsibility: str,
        job_title: str | None,
        department: str | None,
        is_primary: bool,
        is_active: bool,
    ) -> ContactPerson | None:
        contact = await self.get(contact_id)

        if contact is None:
            return None

        contact.name = " ".join(name.split())
        contact.email = email.strip().lower()
        contact.responsibility = " ".join(responsibility.split())
        contact.job_title = " ".join(job_title.split()) if job_title else None
        contact.department = " ".join(department.split()) if department else None
        contact.is_active = is_active

        if is_primary and is_active:
            await self._assign_primary(contact)
        else:
            contact.is_primary = False

        await self.db.commit()
        await self.db.refresh(contact)

        return contact

    async def deactivate(
        self,
        contact_id: uuid.UUID,
    ) -> ContactPerson | None:
        contact = await self.get(contact_id)

        if contact is None:
            return None

        contact.is_active = False
        contact.is_primary = False

        await self.db.commit()
        await self.db.refresh(contact)

        return contact

    async def _assign_primary(
        self,
        contact: ContactPerson,
    ) -> None:
        await self.db.execute(
            update(ContactPerson)
            .where(
                ContactPerson.responsibility == contact.responsibility,
                ContactPerson.is_primary.is_(True),
                ContactPerson.id != contact.id,
            )
            .values(
                is_primary=False,
            )
        )

        await self.db.flush()

        contact.is_primary = True

        await self.db.flush()
