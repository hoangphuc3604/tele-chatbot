"""INKLIU Bot - Main entry point."""

import asyncio
import logging
import os
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

VIETNAM_TZ = timezone(timedelta(hours=7))


class VietnamTimeFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self._fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def format(self, record):
        dt = datetime.fromtimestamp(record.created, tz=VIETNAM_TZ)
        record.asctime = dt.strftime("%Y-%m-%d %H:%M:%S")
        record.msg = str(record.msg)
        record.args = ()
        return self._format(record)

    def _format(self, record):
        return "%s - %s - %s - %s" % (
            record.asctime,
            record.name,
            record.levelname,
            record.getMessage(),
        )


handler = logging.StreamHandler()
formatter = VietnamTimeFormatter()
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

logging.getLogger("aiogram.dispatcher").setLevel(logging.WARNING)
logging.getLogger("aiogram.event").setLevel(logging.WARNING)

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from src.scheduler import scheduler
from src.handlers import register_handlers


logger = logging.getLogger(__name__)


async def main() -> None:
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables")
        return

    bot = Bot(token=bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    scheduler.set_bot(bot)

    register_handlers(dp)

    logger.info("Bot starting...")

    try:
        await scheduler.start()

        await bot.delete_webhook(drop_pending_updates=True)

        await dp.start_polling(bot, drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Error while polling: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        await scheduler.stop()
        if bot.session:
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
