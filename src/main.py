"""INKLIU Bot - Main entry point."""

import asyncio
import logging
import os
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

# Configure Vietnam timezone (+7)
VIETNAM_TZ = timezone(timedelta(hours=7))


class VietnamTimeFormatter(logging.Formatter):
    """Custom formatter that converts UTC to Vietnam timezone."""

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        # Use a simple format with positional args to avoid style validation
        self._fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def format(self, record):
        # Convert UTC timestamp to Vietnam timezone
        dt = datetime.fromtimestamp(record.created, tz=VIETNAM_TZ)
        record.asctime = dt.strftime("%Y-%m-%d %H:%M:%S")
        # Use %s style
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


# Set timezone for logging
handler = logging.StreamHandler()
formatter = VietnamTimeFormatter()
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

# Suppress verbose aiogram polling logs
logging.getLogger("aiogram.dispatcher").setLevel(logging.WARNING)
logging.getLogger("aiogram.event").setLevel(logging.WARNING)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from src.keyboard import get_main_keyboard
from src.agent import process_message
from src.scheduler import scheduler
from src.tools import add_task, list_tasks, get_task, update_task, delete_task
from src.tools import get_or_create_user

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    await message.answer(
        text=(
            "Xin chào {first_name}!\n\n"
            "Tôi là INKLIU Bot - Trợ lý AI cá nhân của bạn.\n\n"
            "Tôi có thể giúp bạn:\n"
            "* Quản lý công việc (thêm, xem, sửa, xóa)\n"
            "* Nhắc nhở deadline\n"
            "* Đặt mục tiêu và theo dõi tiến độ\n\n"
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
            "/help - Xem hướng dẫn\n"
            "/tasks - Xem danh sách công việc\n"
            "/add - Thêm công việc mới\n"
            "/done - Đánh dấu hoàn thành\n"
            "/delete - Xóa công việc\n"
            "/cancel - Hủy công việc\n"
            "/reminders - Xem công việc cần làm\n\n"
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


@router.message(Command("tasks"))
async def cmd_tasks(message: Message) -> None:
    """Handle /tasks command."""
    if not message.from_user:
        return

    user_id = get_or_create_user(message.from_user.id, message.from_user.first_name or "User")
    result = list_tasks.invoke({"user_id": user_id, "limit": 20})
    await message.answer(result, parse_mode="HTML")


@router.message(Command("add"))
async def cmd_add(message: Message) -> None:
    """Handle /add command."""
    if not message.from_user:
        return

    await message.answer(
        text=(
            "➕ <b>Thêm công việc mới</b>\n\n"
            "Vui lòng nhập thông tin task theo format:\n"
            "<code>/add [tiêu đề] | [deadline] | [priority]</code>\n\n"
            "Ví dụ:\n"
            "• <code>/add Làm bài tập | ngày mai 23h | 3</code>\n"
            "• <code>/add Họp team | 20/03/2026 14:00</code>\n"
            "• <code>/add Mua đồ</code>\n\n"
            "Hoặc bạn có thể nhắn tin tự nhiên cho tôi!"
        ),
        parse_mode="HTML",
    )


@router.message(Command("done"))
async def cmd_done(message: Message) -> None:
    """Handle /done command."""
    if not message.from_user:
        return

    user_id = get_or_create_user(message.from_user.id, message.from_user.first_name or "User")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            text=(
                "[X] **Đánh dấu hoàn thành**\n\n"
                "Vui lòng nhập ID task cần hoàn thành:\n"
                "<code>/done [task_id]</code>\n\n"
                "Ví dụ: <code>/done 1</code>\n\n"
                "Xem danh sách task: /tasks"
            ),
            parse_mode="HTML",
        )
        return

    try:
        task_id = int(parts[1].strip())
        result = update_task.invoke({"task_id": task_id, "user_id": user_id, "status": "done"})
        await message.answer(result, parse_mode="HTML")
    except ValueError:
        await message.answer("[Lỗi] ID task không hợp lệ!")


@router.message(Command("delete"))
async def cmd_delete(message: Message) -> None:
    """Handle /delete command."""
    if not message.from_user:
        return

    user_id = get_or_create_user(message.from_user.id, message.from_user.first_name or "User")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            text=(
                "🗑️ <b>Xóa công việc</b>\n\n"
                "Vui lòng nhập ID task cần xóa:\n"
                "<code>/delete [task_id]</code>\n\n"
                "Ví dụ: <code>/delete 1</code>\n\n"
                "Để xóa nhiều task: <code>/delete 1,2,3</code>\n"
                "Xem danh sách task: /tasks"
            ),
            parse_mode="HTML",
        )
        return

    task_ids_str = parts[1].strip()
    try:
        if "," in task_ids_str:
            from src.tools import delete_tasks
            task_ids = ",".join([str(int(tid.strip())) for tid in task_ids_str.split(",")])
            result = delete_tasks.invoke({"user_id": user_id, "task_ids": task_ids})
        else:
            task_id = int(task_ids_str)
            result = delete_task.invoke({"task_id": task_id, "user_id": user_id})
        await message.answer(result, parse_mode="HTML")
    except ValueError:
        await message.answer("[Lỗi] ID task không hợp lệ!")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    """Handle /cancel command."""
    if not message.from_user:
        return

    user_id = get_or_create_user(message.from_user.id, message.from_user.first_name or "User")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            text=(
                "[-] **Hủy công việc**\n\n"
                "Vui lòng nhập ID task cần hủy:\n"
                "<code>/cancel [task_id]</code>\n\n"
                "Ví dụ: <code>/cancel 1</code>\n\n"
                "Xem danh sách task: /tasks"
            ),
            parse_mode="HTML",
        )
        return

    try:
        task_id = int(parts[1].strip())
        result = update_task.invoke({"task_id": task_id, "user_id": user_id, "status": "cancelled"})
        await message.answer(result, parse_mode="HTML")
    except ValueError:
        await message.answer("[Lỗi] ID task không hợp lệ!")


@router.message(Command("reminders"))
async def cmd_reminders(message: Message) -> None:
    """Handle /reminders command."""
    if not message.from_user:
        return

    user_id = get_or_create_user(message.from_user.id, message.from_user.first_name or "User")
    result = list_tasks.invoke({"user_id": user_id, "status": "pending", "limit": 20})
    await message.answer(
        text=f"**Danh sach nhac nho**\n\n{result}",
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
            "[Lỗi] Đã xảy ra lỗi khi xử lý tin nhắn của bạn.\n\n"
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
    dp = Dispatcher(storage=MemoryStorage())

    # Set bot for scheduler
    scheduler.set_bot(bot)

    dp.include_router(router)

    logger.info("Bot starting...")

    try:
        # Start scheduler
        await scheduler.start()

        await bot.delete_webhook(drop_pending_updates=True)
        
        # Using Dispatcher's polling
        await dp.start_polling(bot, drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Error while polling: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        # Stop scheduler
        await scheduler.stop()
        if bot.session:
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
