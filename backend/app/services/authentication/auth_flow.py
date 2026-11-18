from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_flow import AuthFlow
from app.services.authentication.oauth import hash_token


async def consume_auth_flow(
    db: AsyncSession,
    state: str,
    browser_nonce: str,
) -> AuthFlow | None:
    now = datetime.now(timezone.utc)

    statement = (
        update(AuthFlow)
        .where(
            AuthFlow.state_hash == hash_token(state),
            AuthFlow.browser_nonce_hash == hash_token(browser_nonce),
            AuthFlow.expires_at > now,
            AuthFlow.consumed_at.is_(None),
        )
        .values(consumed_at=now)
        .returning(AuthFlow)
    )

    result = await db.execute(statement)
    flow = result.scalar_one_or_none()

    await db.commit()

    return flow
