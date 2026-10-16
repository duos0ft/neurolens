from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.pagination import PageResponse

T = TypeVar("T", bound=BaseModel)


async def paginate(
    db: AsyncSession,
    query: Select,
    *,
    page: int,
    page_size: int,
    response_model: type[T],
    row_mapper: Callable[[Any], Any] | None = None,
) -> PageResponse[T]:
    count_query = select(func.count()).select_from(
        query.order_by(None).limit(None).offset(None).subquery()
    )

    total_items = await db.scalar(count_query) or 0

    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))

    rows = result.all() if row_mapper else result.scalars().all()

    items = [response_model.model_validate(row_mapper(row) if row_mapper else row) for row in rows]

    return PageResponse[T](
        items=items,
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=(total_items + page_size - 1) // page_size,
    )
