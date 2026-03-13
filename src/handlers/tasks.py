from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.tools import add_task, list_tasks, get_task, update_task, delete_task
from src.tools import get_or_create_user


router = Router()


@router.message(Command("tasks"))
async def cmd_tasks(message: Message) -> None:
    if not message.from_user:
        return

    user_id = get_or_create_user(message.from_user.id, message.from_user.first_name or "User")
    result = list_tasks.invoke({"user_id": user_id, "limit": 20})
    await message.answer(result, parse_mode="HTML")


@router.message(Command("add"))
async def cmd_add(message: Message) -> None:
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
    if not message.from_user:
        return

    user_id = get_or_create_user(message.from_user.id, message.from_user.first_name or "User")
    result = list_tasks.invoke({"user_id": user_id, "status": "pending", "limit": 20})
    await message.answer(
        text=f"**Danh sach nhac nho**\n\n{result}",
        parse_mode="HTML",
    )
