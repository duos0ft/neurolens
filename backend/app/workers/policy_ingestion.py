import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import async_session_factory, engine
from app.services.policy.policy_ingestion import PolicyIngestionService

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 5
ERROR_RETRY_SECONDS = 10


class PolicyIngestionRunner:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.processor = PolicyIngestionService(session_factory)

    async def run(self) -> None:
        logger.info("Policy ingestion worker started")

        try:
            while True:
                try:
                    processed = await self.processor.process_next()

                    if not processed:
                        await asyncio.sleep(POLL_INTERVAL_SECONDS)

                except asyncio.CancelledError:
                    raise

                except Exception:
                    logger.exception("Policy ingestion worker encountered an error")

                    await asyncio.sleep(ERROR_RETRY_SECONDS)

        except asyncio.CancelledError:
            logger.info("Policy ingestion worker stopping")
            raise


async def main() -> None:
    try:
        runner = PolicyIngestionRunner(async_session_factory)
        await runner.run()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
