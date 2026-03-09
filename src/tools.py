"""LangChain tools for INKLIU Bot."""

import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from langchain_core.tools import tool

from src.database import get_db_context
from src.models import Task, User

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


class DeleteTaskInput(BaseModel):
    """Input schema for delete_task tool."""
    task_id: int
    user_id: int


class GetTaskInput(BaseModel):
    """Input schema for get_task tool."""
    task_id: int
    user_id: int


def get_or_create_user(telegram_id: int, first_name: str) -> User:
    """Get or create user by telegram ID."""
    with get_db_context() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
            )
            db.add(user)
            db.flush()
        return user


@tool(args_schema=AddTaskInput)
def add_task(
    user_id: int,
    title: str,
    description: Optional[str] = None,
    deadline: Optional[datetime] = None,
    priority: int = 2,
    tags: Optional[str] = None,
    recurring: Optional[str] = None,
) -> str:
    """Thêm task mới cho user.

    Args:
        user_id: ID của user trong database.
        title: Tiêu đề task.
        description: Mô tả chi tiết (optional).
        deadline: Thời hạn hoàn thành (optional).
        priority: Độ ưu tiên 1-4 (1=thấp nhất, 4=cao nhất), mặc định là 2.
        tags: Danh sách tag, phân cách bằng dấu phẩy (optional).
        recurring: Tần suất lặp "daily", "weekly", "monthly" (optional).

    Returns:
        Chuỗi xác nhận task đã được thêm.
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
                status=Task.Status.PENDING,
            )
            db.add(task)
            db.flush()

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
        return f"❌ Lỗi khi thêm task: {str(e)}"


@tool(args_schema=ListTasksInput)
def list_tasks(
    user_id: int,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    limit: int = 10,
) -> str:
    """Liệt kê các task của user.

    Args:
        user_id: ID của user trong database.
        status: Lọc theo trạng thái "pending", "done", "cancelled" (optional).
        priority: Lọc theo độ ưu tiên 1-4 (optional).
        limit: Số lượng task tối đa, mặc định là 10.

    Returns:
        Chuỗi chứa danh sách các task.
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
        return f"❌ Lỗi khi lấy danh sách task: {str(e)}"


@tool(args_schema=GetTaskInput)
def get_task(task_id: int, user_id: int) -> str:
    """Lấy chi tiết một task cụ thể.

    Args:
        task_id: ID của task cần xem.
        user_id: ID của user sở hữu task.

    Returns:
        Chuỗi chứa chi tiết task.
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
        return f"❌ Lỗi khi lấy chi tiết task: {str(e)}"


@tool(args_schema=UpdateTaskInput)
def update_task(
    task_id: int,
    user_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    deadline: Optional[datetime] = None,
    priority: Optional[int] = None,
    status: Optional[str] = None,
) -> str:
    """Cập nhật thông tin task.

    Args:
        task_id: ID của task cần cập nhật.
        user_id: ID của user sở hữu task.
        title: Tiêu đề mới (optional).
        description: Mô tả mới (optional).
        deadline: Deadline mới (optional).
        priority: Priority mới 1-4 (optional).
        status: Trạng thái mới "pending", "done", "cancelled" (optional).

    Returns:
        Chuỗi xác nhận đã cập nhật.
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
            if status is not None:
                if status in [Task.Status.PENDING, Task.Status.DONE, Task.Status.CANCELLED]:
                    task.status = status

            db.flush()

            return f"✅ Đã cập nhật task ID {task_id}!"
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return f"❌ Lỗi khi cập nhật task: {str(e)}"


@tool(args_schema=DeleteTaskInput)
def delete_task(task_id: int, user_id: int) -> str:
    """Xóa một task.

    Args:
        task_id: ID của task cần xóa.
        user_id: ID của user sở hữu task.

    Returns:
        Chuỗi xác nhận đã xóa.
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
            db.delete(task)

            return f"✅ Đã xóa task: {task_title}"
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        return f"❌ Lỗi khi xóa task: {str(e)}"
