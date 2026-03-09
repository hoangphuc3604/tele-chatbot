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
from src.agent import process_message

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


@router.message()
async def handle_message(message: Message) -> None:
    """Handle regular text messages with AI agent."""
    if not message.text:
        return

    if not message.from_user:
        return

    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    user_message = message.text

    logger.info(f"Message from {user_id}: {user_message}")

    # Send "typing" action
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Process message with agent
        response = await process_message(user_id, user_message, first_name)
        # Send response
        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        # Send user-friendly error message
        error_msg = (
            "❌ Đã xảy ra lỗi khi xử lý tin nhắn của bạn.\n\n"
            "Vui lòng thử lại sau hoặc liên hệ hỗ trợ nếu lỗi tiếp tục xảy ra."
        )
        await message.answer(error_msg)


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
