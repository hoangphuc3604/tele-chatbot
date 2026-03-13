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
            "/start - Khoi dong bot\n"
            "/help - Xem huong dan\n"
            "/test - Test HTML formatting\n"
            "/licham - Xem lich am\n"
            "/lichduong - Xem lich duong\n"
            "/tasks - Xem danh sach cong viec\n"
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


@router.message(Command("licham"))
async def cmd_licham(message: Message) -> None:
    from datetime import date

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        today = date.today()
        month = today.month
        year = today.year
    else:
        param = parts[1].strip()
        try:
            month = int(param)
            if month < 1 or month > 12:
                await message.answer("Thang phai tu 1-12!")
                return
            today = date.today()
            year = today.year
        except ValueError:
            await message.answer("Vui long nhap so thang hop le (1-12).\n\nVi du: /licham 3")
            return

    from src.keyboard import get_calendar_keyboard
    keyboard = get_calendar_keyboard(month, year)
    await message.answer(
        f"<b>Lich Am - Thang {month} {year}</b>\n\nChon ngay de xem chi tiet:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("lichduong"))
async def cmd_lichduong(message: Message) -> None:
    from datetime import date

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        today = date.today()
        month = today.month
        year = today.year
    else:
        param = parts[1].strip()
        try:
            month = int(param)
            if month < 1 or month > 12:
                await message.answer("Thang phai tu 1-12!")
                return
            today = date.today()
            year = today.year
        except ValueError:
            await message.answer("Vui long nhap so thang hop le (1-12).\n\nVi du: /lichduong 3")
            return

    from src.keyboard import get_solar_calendar_keyboard
    keyboard = get_solar_calendar_keyboard(month, year)
    await message.answer(
        f"<b>Lich Duong - Thang {month} {year}</b>\n\nHien thi ngay duong + ngay am:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
