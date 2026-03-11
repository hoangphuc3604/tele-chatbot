"""LangChain tools for INKLIU Bot."""

import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from langchain_core.tools import tool

from src.database import get_db_context
from src.models import Task, User, ImportantDate, ConversationHistory
from src.scheduler import scheduler
from src.holidays import (
    get_upcoming_holidays as get_holidays_from_service,
    convert_lunar_to_solar,
    convert_solar_to_lunar,
    format_date_vietnamese,
    get_vietnam_date,
)

logger = logging.getLogger(__name__)


class AddTaskInput(BaseModel):
    """Input schema for add_task tool."""
    user_id: int
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: int = 2
    tags: Optional[str] = None
    recurring: Optional[str] = None
    reminder_minutes: Optional[int] = 30


class ListTasksInput(BaseModel):
    """Input schema for list_tasks tool."""
    user_id: int
    status: Optional[str] = None
    priority: Optional[int] = None
    limit: int = 10


class UpdateTaskInput(BaseModel):
    """Input schema for update_task tool."""
    task_id: int
    user_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[int] = None
    status: Optional[str] = None
    reminder_minutes: Optional[int] = None


class DeleteTaskInput(BaseModel):
    """Input schema for delete_task tool."""
    task_id: int
    user_id: int


class DeleteTasksInput(BaseModel):
    """Input schema for delete_tasks tool."""
    user_id: int
    task_ids: Optional[str] = None
    status: Optional[str] = None
    delete_all: bool = False


class GetTaskInput(BaseModel):
    """Input schema for get_task tool."""
    task_id: int
    user_id: int


def get_or_create_user(telegram_id: int, first_name: str) -> int:
    """Get or create user by telegram ID.

    Args:
        telegram_id: Telegram user ID.
        first_name: User's first name.

    Returns:
        Database user ID (primary key).
    """
    with get_db_context() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
            )
            db.add(user)
            db.flush()
        return user.id


@tool(args_schema=AddTaskInput)
def add_task(
    user_id: int,
    title: str,
    description: Optional[str] = None,
    deadline: Optional[datetime] = None,
    priority: int = 2,
    tags: Optional[str] = None,
    recurring: Optional[str] = None,
    reminder_minutes: Optional[int] = 30,
) -> str:
    """Add a new task for the user.

    Args:
        user_id: Database user ID.
        title: Task title.
        description: Task description (optional).
        deadline: Due date for completion (optional).
        priority: Priority level 1-4 (1=lowest, 4=highest), default is 2.
        tags: Comma-separated tags (optional).
        recurring: Recurrence frequency "daily", "weekly", "monthly" (optional).

    Returns:
        Confirmation message with task details.
    """
    try:
        with get_db_context() as db:
            task = Task(
                user_id=user_id,
                title=title,
                description=description,
                deadline=deadline,
                priority=priority,
                tags=tags,
                recurring=recurring,
                reminder_minutes=reminder_minutes,
                status=Task.Status.PENDING,
            )
            db.add(task)
            db.flush()

            logger.info(
                f"Task {task.id} created: title='{title}', "
                f"deadline={deadline}, reminder_minutes={reminder_minutes}"
            )

            if task.deadline and task.reminder_minutes is not None:
                scheduler.schedule_reminder(task)

            deadline_str = deadline.strftime("%d/%m/%Y %H:%M") if deadline else "không có deadline"
            priority_text = {1: "thấp", 2: "trung bình", 3: "cao", 4: "khẩn cấp"}

            return (
                f"[OK] Đã thêm task mới!\n\n"
                f"<b>{title}</b>\n"
                f"Deadline: {deadline_str}\n"
                f"Priority: {priority_text.get(priority, 'trung bình')}\n"
                f"Task ID: {task.id}"
            )
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        return "[Lỗi] Lỗi khi thêm task. Vui lòng thử lại sau."


@tool(args_schema=ListTasksInput)
def list_tasks(
    user_id: int,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    limit: int = 10,
) -> str:
    """List all tasks for the user.

    Args:
        user_id: Database user ID.
        status: Filter by status "pending", "done", "cancelled" (optional).
        priority: Filter by priority level 1-4 (optional).
        limit: Maximum number of tasks, default is 10.

    Returns:
        Formatted string containing the task list.
    """
    try:
        with get_db_context() as db:
            query = db.query(Task).filter(Task.user_id == user_id)

            if status:
                query = query.filter(Task.status == status)
            if priority:
                query = query.filter(Task.priority == priority)

            tasks = query.order_by(Task.priority.desc(), Task.deadline.asc()).limit(limit).all()

            if not tasks:
                return "[Danh sách] Bạn chưa có task nào!"

            result = "[Danh sách] <b>Công việc:</b>\n\n"
            for i, task in enumerate(tasks, 1):
                status_mark = "[X]" if task.status == Task.Status.DONE else "[ ]"
                priority_mark = "[Cao]" if task.priority >= 3 else "[TB]" if task.priority >= 2 else "[Thấp]"
                deadline_str = task.deadline.strftime("%d/%m/%Y %H:%M") if task.deadline else "không deadline"

                result += (
                    f"{i}. {status_mark} <b>{task.title}</b>\n"
                    f"   ID: {task.id} | {priority_mark} Priority {task.priority} | Deadline: {deadline_str}\n"
                )

            pending_count = sum(1 for t in tasks if t.status == Task.Status.PENDING)
            result += f"\nTổng: {len(tasks)} task | Chờ: {pending_count}"

            return result
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return "[Lỗi] Lỗi khi lấy danh sách task. Vui lòng thử lại sau."


@tool(args_schema=GetTaskInput)
def get_task(task_id: int, user_id: int) -> str:
    """Get details of a specific task.

    Args:
        task_id: Task ID to retrieve.
        user_id: Database user ID who owns the task.

    Returns:
        Formatted string containing task details.
    """
    try:
        with get_db_context() as db:
            task = db.query(Task).filter(
                Task.id == task_id,
                Task.user_id == user_id,
            ).first()

            if not task:
                return "[Lỗi] Task không tồn tại!"

            status_text = {
                Task.Status.PENDING: "[ ] Chờ xử lý",
                Task.Status.DONE: "[X] Hoàn thành",
                Task.Status.CANCELLED: "[-] Đã hủy",
            }
            priority_text = {1: "Thấp", 2: "Trung bình", 3: "Cao", 4: "Khẩn cấp"}

            result = (
                f"<b>Chi tiết Task</b>\n\n"
                f"ID: {task.id}\n"
                f"Tiêu đề: {task.title}\n"
            )

            if task.description:
                result += f"Mô tả: {task.description}\n"

            result += (
                f"Trạng thái: {status_text.get(task.status, task.status)}\n"
                f"Priority: {priority_text.get(task.priority, 'Trung bình')}\n"
            )

            if task.deadline:
                result += f"Deadline: {task.deadline.strftime('%d/%m/%Y %H:%M')}\n"

            if task.tags:
                result += f"Tags: {task.tags}\n"

            if task.recurring:
                result += f"Lặp: {task.recurring}\n"

            return result
    except Exception as e:
        logger.error(f"Error getting task: {e}")
        return "[Lỗi] Lỗi khi lấy chi tiết task. Vui lòng thử lại sau."


@tool(args_schema=UpdateTaskInput)
def update_task(
    task_id: int,
    user_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    deadline: Optional[datetime] = None,
    priority: Optional[int] = None,
    status: Optional[str] = None,
    reminder_minutes: Optional[int] = None,
) -> str:
    """Update task information.

    Args:
        task_id: Task ID to update.
        user_id: Database user ID who owns the task.
        title: New title (optional).
        description: New description (optional).
        deadline: New deadline (optional).
        priority: New priority level 1-4 (optional).
        status: New status "pending", "done", "cancelled" (optional).

    Returns:
        Confirmation message.
    """
    try:
        with get_db_context() as db:
            task = db.query(Task).filter(
                Task.id == task_id,
                Task.user_id == user_id,
            ).first()

            if not task:
                return "[Lỗi] Task không tồn tại!"

            if title is not None:
                task.title = title
            if description is not None:
                task.description = description
            if deadline is not None:
                task.deadline = deadline
            if priority is not None:
                task.priority = priority
            if reminder_minutes is not None:
                task.reminder_minutes = reminder_minutes
                if task.deadline and task.reminder_minutes:
                    scheduler.cancel_reminder(task_id)
                    scheduler.schedule_reminder(task)
            if status is not None:
                if status in [Task.Status.PENDING, Task.Status.DONE, Task.Status.CANCELLED]:
                    task.status = status
                    if status != Task.Status.PENDING:
                        scheduler.cancel_reminder(task_id)
            if deadline is not None:
                task.deadline = deadline
                if task.deadline and task.reminder_minutes:
                    scheduler.cancel_reminder(task_id)
                    scheduler.schedule_reminder(task)

            db.flush()

            return f"[OK] Đã cập nhật task ID {task_id}!"
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return "[Lỗi] Lỗi khi cập nhật task. Vui lòng thử lại sau."


@tool(args_schema=DeleteTaskInput)
def delete_task(task_id: int, user_id: int) -> str:
    """Delete a task.

    Args:
        task_id: Task ID to delete.
        user_id: Database user ID who owns the task.

    Returns:
        Confirmation message.
    """
    try:
        with get_db_context() as db:
            task = db.query(Task).filter(
                Task.id == task_id,
                Task.user_id == user_id,
            ).first()

            if not task:
                return "[Lỗi] Task không tồn tại!"

            task_title = task.title
            scheduler.cancel_reminder(task_id)
            db.delete(task)

            return f"[OK] Đã xóa task: {task_title}"
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        return "[Lỗi] Lỗi khi xóa task. Vui lòng thử lại sau."


@tool(args_schema=DeleteTasksInput)
def delete_tasks(
    user_id: int,
    task_ids: Optional[str] = None,
    status: Optional[str] = None,
    delete_all: bool = False,
) -> str:
    """Delete multiple tasks at once.

    Args:
        user_id: Database user ID.
        task_ids: Comma-separated task IDs (e.g., "1,2,3").
        status: Filter by status "pending", "done", "cancelled".
        delete_all: If True, delete all user tasks.

    Returns:
        Confirmation message with number of deleted tasks.
    """
    try:
        with get_db_context() as db:
            query = db.query(Task).filter(Task.user_id == user_id)

            if delete_all:
                tasks_to_delete = query.all()
            elif status:
                if status not in [Task.Status.PENDING, Task.Status.DONE, Task.Status.CANCELLED]:
                    return "[Lỗi] Trạng thái không hợp lệ!"
                tasks_to_delete = query.filter(Task.status == status).all()
            elif task_ids:
                try:
                    task_id_list = [int(tid.strip()) for tid in task_ids.split(",")]
                except ValueError:
                    return "[Lỗi] ID task không hợp lệ!"
                tasks_to_delete = query.filter(Task.id.in_(task_id_list)).all()
            else:
                return "[Lỗi] Vui lòng chọn task_ids, status, hoặc delete_all!"

            if not tasks_to_delete:
                return "[Lỗi] Không có task nào để xóa!"

            deleted_count = 0
            for task in tasks_to_delete:
                scheduler.cancel_reminder(task.id)
                db.delete(task)
                deleted_count += 1

            return f"[OK] Đã xóa {deleted_count} task!"
    except Exception as e:
        logger.error(f"Error deleting tasks: {e}")
        return "[Lỗi] Lỗi khi xóa task. Vui lòng thử lại sau."


class AddImportantDateInput(BaseModel):
    """Input schema for add_important_date tool."""
    user_id: int
    title: str
    date_type: str = "lunar"
    month: int
    day: int
    year: Optional[int] = None
    description: Optional[str] = None
    reminder_days_before: int = 3
    recurring_type: str = "yearly"


class ListImportantDatesInput(BaseModel):
    """Input schema for list_important_dates tool."""
    user_id: int


class DeleteImportantDateInput(BaseModel):
    """Input schema for delete_important_date tool."""
    date_id: int
    user_id: int


class GetUpcomingHolidaysInput(BaseModel):
    """Input schema for get_upcoming_holidays tool."""
    days: int = 30


class ConvertCalendarInput(BaseModel):
    """Input schema for convert_calendar tool."""
    date: str
    from_type: str
    to_type: str


@tool(args_schema=AddImportantDateInput)
def add_important_date(
    user_id: int,
    title: str,
    month: int,
    day: int,
    date_type: str = "lunar",
    year: Optional[int] = None,
    description: Optional[str] = None,
    reminder_days_before: int = 3,
    recurring_type: str = "yearly",
) -> str:
    """Add a new important date for the user (birthday, anniversary, etc.).

    Args:
        user_id: Database user ID.
        title: Title of the important date (e.g., "Sinh nhật mẹ").
        date_type: "lunar" for lunar calendar, "solar" for solar calendar.
        month: Month (1-12).
        day: Day (1-30).
        year: Year (optional, for non-recurring dates).
        description: Additional description (optional).
        reminder_days_before: Days before to send reminder (default: 3).
        recurring_type: "daily", "weekly", "monthly", "yearly", or "none" (default: yearly).

    Returns:
        Confirmation message with date details.
    """
    try:
        if month < 1 or month > 12:
            return "[Lỗi] Tháng phải từ 1-12!"

        if day < 1 or day > 30:
            return "[Lỗi] Ngày phải từ 1-30!"

        if date_type not in ["lunar", "solar"]:
            return "[Lỗi] date_type phải là 'lunar' hoặc 'solar'!"

        valid_recurring = ["daily", "weekly", "monthly", "yearly", "none"]
        if recurring_type not in valid_recurring:
            return f"[Lỗi] recurring_type phải là một trong: {', '.join(valid_recurring)}"

        with get_db_context() as db:
            important_date = ImportantDate(
                user_id=user_id,
                title=title,
                date_type=date_type,
                month=month,
                day=day,
                year=year,
                description=description,
                reminder_days_before=reminder_days_before,
                is_recurring=year is None,
                recurring_type=recurring_type,
            )
            db.add(important_date)
            db.flush()

            scheduler.schedule_important_date_reminder(important_date)

            date_type_text = "Âm lịch" if date_type == "lunar" else "Dương lịch"
            recurring_text = {
                "daily": "Hàng ngày",
                "weekly": "Hàng tuần",
                "monthly": "Hàng tháng",
                "yearly": "Hàng năm",
                "none": "Một lần",
            }.get(recurring_type, "Hàng năm")

            return (
                f"[OK] Đã thêm ngày quan trọng!\n\n"
                f"<b>{title}</b>\n"
                f"Ngày: {day:02d}/{month:02d} ({date_type_text})\n"
                f"Lặp: {recurring_text}\n"
                f"Nhắc trước: {reminder_days_before} ngày\n"
                f"ID: {important_date.id}"
            )
    except Exception as e:
        logger.error(f"Error adding important date: {e}")
        return "[Lỗi] Lỗi khi thêm ngày quan trọng. Vui lòng thử lại sau."


@tool(args_schema=ListImportantDatesInput)
def list_important_dates(user_id: int) -> str:
    """List all important dates for the user.

    Args:
        user_id: Database user ID.

    Returns:
        Formatted string containing the important dates list.
    """
    try:
        with get_db_context() as db:
            dates = db.query(ImportantDate).filter(
                ImportantDate.user_id == user_id
            ).all()

            if not dates:
                return "[Danh sách] Bạn chưa có ngày quan trọng nào!"

            today = get_vietnam_date()
            result = "[Danh sách] <b>Ngày quan trọng:</b>\n\n"

            for i, date in enumerate(dates, 1):
                if date.date_type == ImportantDate.DateType.LUNAR:
                    try:
                        solar_date = convert_lunar_to_solar(
                            date.month, date.day, today.year
                        )
                        days_until = (solar_date - today).days
                        if days_until < 0:
                            solar_date = convert_lunar_to_solar(
                                date.month, date.day, today.year + 1
                            )
                            days_until = (solar_date - today).days
                    except Exception:
                        days_until = -1
                else:
                    from datetime import date as date_class
                    date_solar = date_class(today.year, date.month, date.day)
                    if date_solar < today:
                        date_solar = date_class(today.year + 1, date.month, date.day)
                    days_until = (date_solar - today).days

                date_type_text = "Âm" if date.date_type == ImportantDate.DateType.LUNAR else "Dương"
                recurring_text_map = {
                    ImportantDate.RecurringType.DAILY: " (hàng ngày)",
                    ImportantDate.RecurringType.WEEKLY: " (hàng tuần)",
                    ImportantDate.RecurringType.MONTHLY: " (hàng tháng)",
                    ImportantDate.RecurringType.YEARLY: " (hàng năm)",
                    ImportantDate.RecurringType.NONE: " (một lần)",
                }
                recurring_text = recurring_text_map.get(date.recurring_type, "")

                result += (
                    f"{i}. <b>{date.title}</b>\n"
                    f"   ID: {date.id} | {date.day:02d}/{date.month:02d} ({date_type_text}){recurring_text}\n"
                    f"   Còn {days_until} ngày nữa\n"
                )

            return result
    except Exception as e:
        logger.error(f"Error listing important dates: {e}")
        return "[Lỗi] Lỗi khi lấy danh sách ngày quan trọng. Vui lòng thử lại sau."


@tool(args_schema=DeleteImportantDateInput)
def delete_important_date(date_id: int, user_id: int) -> str:
    """Delete an important date.

    Args:
        date_id: Important date ID to delete.
        user_id: Database user ID who owns the date.

    Returns:
        Confirmation message.
    """
    try:
        with get_db_context() as db:
            date = db.query(ImportantDate).filter(
                ImportantDate.id == date_id,
                ImportantDate.user_id == user_id,
            ).first()

            if not date:
                return "[Lỗi] Ngày quan trọng không tồn tại!"

            date_title = date.title
            scheduler.cancel_important_date_reminder(date_id)
            db.delete(date)

            return f"[OK] Đã xóa ngày quan trọng: {date_title}"
    except Exception as e:
        logger.error(f"Error deleting important date: {e}")
        return "[Lỗi] Lỗi khi xóa ngày quan trọng. Vui lòng thử lại sau."


@tool(args_schema=GetUpcomingHolidaysInput)
def get_upcoming_holidays(days: int = 30) -> str:
    """Get upcoming Vietnam holidays.

    Args:
        days: Number of days ahead to check (default: 30).

    Returns:
        Formatted string containing upcoming holidays.
    """
    try:
        holidays = get_holidays_from_service(days)

        if not holidays:
            return f"[Danh sách] Không có lễ hội nào trong {days} ngày tới!"

        result = f"[Danh sách] <b>Lễ hội Việt Nam</b> (trong {days} ngày):\n\n"

        for holiday in holidays:
            date_type_text = "Âm" if holiday["date_type"] == "lunar" else "Dương"
            result += (
                f"- <b>{holiday['name']}</b>\n"
                f"  Ngày: {holiday['date'].strftime('%d/%m/%Y')} ({date_type_text})\n"
                f"  Còn {holiday['days_until']} ngày\n\n"
            )

        return result
    except Exception as e:
        logger.error(f"Error getting upcoming holidays: {e}")
        return "[Lỗi] Lỗi khi lấy danh sách lễ hội. Vui lòng thử lại sau."


@tool(args_schema=ConvertCalendarInput)
def convert_calendar(date: str, from_type: str, to_type: str) -> str:
    """Convert date between lunar and solar calendar.

    Args:
        date: Date in DD/MM/YYYY format.
        from_type: Source calendar type ("lunar" or "solar").
        to_type: Target calendar type ("lunar" or "solar").

    Returns:
        Converted date in Vietnamese format.
    """
    try:
        from datetime import datetime as dt

        parts = date.split("/")
        if len(parts) != 3:
            return "[Lỗi] Định dạng ngày không hợp lệ! Vui dùng DD/MM/YYYY"

        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2])

        if from_type not in ["lunar", "solar"] or to_type not in ["lunar", "solar"]:
            return "[Lỗi] calendar_type phải là 'lunar' hoặc 'solar'!"

        if from_type == to_type:
            return f"Ngày {date} ({from_type}) = {date} ({to_type})"

        if from_type == "lunar" and to_type == "solar":
            solar_date = convert_lunar_to_solar(month, day, year)
            return (
                f"Ngày {date} (Âm lịch) = {solar_date.strftime('%d/%m/%Y')} (Dương lịch)"
            )
        else:
            lunar_month, lunar_day = convert_solar_to_lunar(month, day, year)
            return (
                f"Ngày {date} (Dương lịch) = {lunar_day:02d}/{lunar_month:02d}/{year} (Âm lịch)"
            )
    except Exception as e:
        logger.error(f"Error converting calendar: {e}")
        return "[Lỗi] Lỗi khi chuyển đổi lịch. Vui lòng kiểm tra định dạng ngày!"


def save_conversation_message(
    user_id: int,
    role: str,
    content: str,
) -> None:
    """Lưu tin nhắn vào lịch sử chat."""
    with get_db_context() as db:
        message = ConversationHistory(
            user_id=user_id,
            role=role,
            content=content,
        )
        db.add(message)


def get_conversation_history(
    user_id: int,
    limit: int = 10,
) -> list[dict]:
    """Lấy lịch sử chat gần nhất."""
    with get_db_context() as db:
        messages = (
            db.query(ConversationHistory)
            .filter(ConversationHistory.user_id == user_id)
            .order_by(ConversationHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {"role": m.role, "content": m.content}
            for m in reversed(messages)
        ]
