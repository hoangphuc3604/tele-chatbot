"""INKLIU Bot - Main entry point."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from src.keyboard import get_main_keyboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    await message.answer(
        text=(
            "👋 Xin chào {first_name}!\n\n"
            "Tôi là INKLIU Bot - Trợ lý AI cá nhân của bạn.\n\n"
            "Tôi có thể giúp bạn:\n"
            "• 📝 Quản lý công việc (thêm, xem, sửa, xóa)\n"
            "• ⏰ Nhắc nhở deadline\n"
            "• 🎯 Đặt mục tiêu và theo dõi tiến độ\n\n"
            "Gõ /help để xem các lệnh có sẵn."
        ).format(first_name=message.from_user.first_name),
        reply_markup=get_main_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    await message.answer(
        text=(
            "📖 <b>Hướng dẫn sử dụng</b>\n\n"
            "<b>Các lệnh cơ bản:</b>\n"
            "/start - Khởi động bot\n"
            "/help - Xem hướng dẫn\n\n"
            "<b>Cách sử dụng:</b>\n"
            "Bạn có thể nhắn tin cho tôi bằng ngôn ngữ tự nhiên.\n"
            "Ví dụ:\n"
            "• \"Thêm task làm bài tập toán ngày mai 23h\"\n"
            "• \"Liệt kê các task của tôi\"\n"
            "• \"Task nào quan trọng nhất\"\n\n"
            "Tôi sẽ hiểu và giúp bạn quản lý công việc!"
        ),
        parse_mode="HTML",
    )


async def main() -> None:
    """Main function to run the bot."""
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables")
        return

    bot = Bot(token=bot_token)
    dp = Dispatcher()

    dp.include_router(router)

    logger.info("Bot starting...")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error while polling: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
