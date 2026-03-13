from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.keyboard import get_main_keyboard


router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
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
    await message.answer(
        text=(
            "📖 <b>Hướng dẫn sử dụng</b>\n\n"
            "<b>Các lệnh cơ bản:</b>\n"
            "/start - Khởi động bot\n"
            "/help - Xem hướng dẫn\n"
            "/test - Test HTML formatting\n"
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


@router.message(Command("test"))
async def cmd_test(message: Message) -> None:
    await message.answer(
        text=(
            "<b>Test HTML Formatting</b>\n\n"
            "<code>Code block</code>\n\n"
            "<i>Italic text</i>\n\n"
            "<b>Bold text</b>\n\n"
            "<u>Underlined text</u>\n\n"
            "<s>Strikethrough text</s>\n\n"
            "<a href='https://google.com'>Link</a>\n\n"
            "<pre>Preformatted text\nwith newlines</pre>\n\n"
            "Emoji: ✅ ❌ 🔥 💯"
        ),
        parse_mode="HTML",
    )
