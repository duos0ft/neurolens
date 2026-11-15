import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import async_session_factory, engine
from app.services.calendar_sync_processor import CalendarSyncProcessor


logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 5
PROCESS_TIMEOUT_SECONDS = 90
ERROR_RETRY_SECONDS = 10


class CalendarSyncRunner:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.processor = CalendarSyncProcessor(session_factory)

    async def run(self) -> None:
        logger.info("Calendar synchronization worker started")

        try:
            while True:
                try:
                    processed = await asyncio.wait_for(
                        self.processor.process_next(),
                        timeout=PROCESS_TIMEOUT_SECONDS,
                    )

                    if not processed:
                        await asyncio.sleep(POLL_INTERVAL_SECONDS)

                except TimeoutError:
                    logger.warning("Calendar synchronization job exceeded processing timeout")

                except Exception:
                    logger.exception("Calendar synchronization worker encountered an error")

                    await asyncio.sleep(ERROR_RETRY_SECONDS)

        except asyncio.CancelledError:
            logger.info("Calendar synchronization worker stopping")
            raise


async def main() -> None:
    try:
        runner = CalendarSyncRunner(async_session_factory)
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
