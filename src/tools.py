"""LangChain tools for INKLIU Bot."""

import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from langchain_core.tools import tool

from src.database import get_db_context
from src.models import Task, User
from src.scheduler import scheduler

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
                f"✅ Đã thêm task mới!\n\n"
                f"📝 <b>{title}</b>\n"
                f"⏰ Deadline: {deadline_str}\n"
                f"🔢 Priority: {priority_text.get(priority, 'trung bình')}\n"
                f"🆔 Task ID: {task.id}"
            )
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        return "❌ Lỗi khi thêm task. Vui lòng thử lại sau."


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
                return "📋 Bạn chưa có task nào!"

            result = "📋 <b>Danh sách công việc:</b>\n\n"
            for i, task in enumerate(tasks, 1):
                status_emoji = "✅" if task.status == Task.Status.DONE else "⏳"
                priority_emoji = "🔴" if task.priority >= 3 else "🟡" if task.priority >= 2 else "🟢"
                deadline_str = task.deadline.strftime("%d/%m/%Y %H:%M") if task.deadline else "không deadline"

                result += (
                    f"{i}. {status_emoji} <b>{task.title}</b>\n"
                    f"   🆔 ID: {task.id} | {priority_emoji} Priority {task.priority} | ⏰ {deadline_str}\n"
                )

            pending_count = sum(1 for t in tasks if t.status == Task.Status.PENDING)
            result += f"\n📊 Tổng: {len(tasks)} task | ⏳ Chờ: {pending_count}"

            return result
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return "❌ Lỗi khi lấy danh sách task. Vui lòng thử lại sau."


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
                return "❌ Task không tồn tại!"

            status_text = {
                Task.Status.PENDING: "⏳ Chờ xử lý",
                Task.Status.DONE: "✅ Hoàn thành",
                Task.Status.CANCELLED: "❌ Đã hủy",
            }
            priority_text = {1: "Thấp", 2: "Trung bình", 3: "Cao", 4: "Khẩn cấp"}

            result = (
                f"📝 <b>Chi tiết Task</b>\n\n"
                f"🆔 ID: {task.id}\n"
                f"📌 Tiêu đề: {task.title}\n"
            )

            if task.description:
                result += f"📄 Mô tả: {task.description}\n"

            result += (
                f"📊 Trạng thái: {status_text.get(task.status, task.status)}\n"
                f"🔢 Priority: {priority_text.get(task.priority, 'Trung bình')}\n"
            )

            if task.deadline:
                result += f"⏰ Deadline: {task.deadline.strftime('%d/%m/%Y %H:%M')}\n"

            if task.tags:
                result += f"🏷️ Tags: {task.tags}\n"

            if task.recurring:
                result += f"🔄 Lặp: {task.recurring}\n"

            return result
    except Exception as e:
        logger.error(f"Error getting task: {e}")
        return "❌ Lỗi khi lấy chi tiết task. Vui lòng thử lại sau."


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
                return "❌ Task không tồn tại!"

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

            return f"✅ Đã cập nhật task ID {task_id}!"
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return "❌ Lỗi khi cập nhật task. Vui lòng thử lại sau."


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
                return "❌ Task không tồn tại!"

            task_title = task.title
            scheduler.cancel_reminder(task_id)
            db.delete(task)

            return f"✅ Đã xóa task: {task_title}"
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        return "❌ Lỗi khi xóa task. Vui lòng thử lại sau."


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
                    return "❌ Trạng thái không hợp lệ!"
                tasks_to_delete = query.filter(Task.status == status).all()
            elif task_ids:
                try:
                    task_id_list = [int(tid.strip()) for tid in task_ids.split(",")]
                except ValueError:
                    return "❌ ID task không hợp lệ!"
                tasks_to_delete = query.filter(Task.id.in_(task_id_list)).all()
            else:
                return "❌ Vui lòng chọn task_ids, status, hoặc delete_all!"

            if not tasks_to_delete:
                return "❌ Không có task nào để xóa!"

            deleted_count = 0
            for task in tasks_to_delete:
                scheduler.cancel_reminder(task.id)
                db.delete(task)
                deleted_count += 1

            return f"✅ Đã xóa {deleted_count} task!"
    except Exception as e:
        logger.error(f"Error deleting tasks: {e}")
        return "❌ Lỗi khi xóa task. Vui lòng thử lại sau."
