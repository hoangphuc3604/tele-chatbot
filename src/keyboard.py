"""Inline keyboards for INKLIU Bot."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Get main keyboard with action buttons."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Thêm Task",
                    callback_data="add_task",
                ),
                InlineKeyboardButton(
                    text="📋 Danh sách Task",
                    callback_data="list_tasks",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⏰ Nhắc nhở",
                    callback_data="reminders",
                ),
                InlineKeyboardButton(
                    text="❓ Trợ giúp",
                    callback_data="help",
                ),
            ],
        ]
    )
    return keyboard


def get_task_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for task actions."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Hoàn thành",
                    callback_data="task_done",
                ),
                InlineKeyboardButton(
                    text="✏️ Sửa",
                    callback_data="task_edit",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Xóa",
                    callback_data="task_delete",
                ),
                InlineKeyboardButton(
                    text="⬅️ Quay lại",
                    callback_data="back_to_main",
                ),
            ],
        ]
    )
    return keyboard


def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Get confirmation keyboard."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Xác nhận",
                    callback_data=f"confirm_{action}",
                ),
                InlineKeyboardButton(
                    text="❌ Hủy",
                    callback_data=f"cancel_{action}",
                ),
            ],
        ]
    )
    return keyboard
