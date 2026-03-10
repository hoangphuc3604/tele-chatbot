"""Celery tasks for INKLIU Bot."""

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.celery_app import celery_app
from src.database import SessionLocal
from src.models import Task, User

logger = logging.getLogger(__name__)

VIETNAM_TZ = timezone(timedelta(hours=7))


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_reminder(self, task_id: int) -> str:
    """Send reminder for a task to Telegram user.

    Args:
        task_id: Database task ID.

    Returns:
        Confirmation message.
    """
    db = SessionLocal()
    bot = None
    try:
        task = db.query(Task).filter(Task.id == task_id).first()

        if not task:
            logger.warning(f"Task {task_id} not found for reminder")
            return f"Task {task_id} not found"

        if task.status != Task.Status.PENDING:
            logger.info(f"Task {task_id} is not pending, skipping reminder")
            return f"Task {task_id} is not pending"

        user = db.query(User).filter(User.id == task.user_id).first()
        if not user:
            logger.warning(f"User not found for task {task_id}")
            return f"User not found for task {task_id}"

        priority_emoji = {
            1: "🟢",
            2: "🟡",
            3: "🟠",
            4: "🔴",
        }

        emoji = priority_emoji.get(task.priority, "🟡")

        deadline_str = (
            task.deadline.strftime("%H:%M %d/%m/%Y") if task.deadline else ""
        )

        message = (
            f"⏰ <b>Nhắc nhở deadline!</b>\n\n"
            f"{emoji} <b>{task.title}</b>\n"
            f"📅 Đến hạn: {deadline_str}\n"
        )

        if task.description:
            message += f"\n📝 {task.description}"

        logger.info(f"Sending reminder for task {task.id} to user {user.telegram_id}")

        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            logger.error("BOT_TOKEN not found in environment")
            raise ValueError("BOT_TOKEN not configured")

        bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        import asyncio

        async def send_telegram_message():
            await bot.send_message(chat_id=user.telegram_id, text=message)

        asyncio.run(send_telegram_message())

        logger.info(f"Reminder sent successfully for task {task.id} to user {user.telegram_id}")

        return f"Reminder sent to user {user.telegram_id}"

    except Exception as e:
        logger.error(f"Failed to send reminder for task {task_id}: {e}")
        raise self.retry(exc=e)
    finally:
        if bot:
            import asyncio
            asyncio.run(bot.session.close())
        db.close()


def schedule_reminder(task: Task) -> Optional[str]:
    """Schedule a reminder for a task using Celery.

    Args:
        task: Task object with deadline and reminder_minutes.

    Returns:
        Task ID or None if not scheduled.
    """
    if not task.deadline:
        logger.info(f"Task {task.id} has no deadline")
        return None

    if task.reminder_minutes is None:
        logger.info(f"Task {task.id} has no reminder_minutes")
        return None

    reminder_time = task.deadline - timedelta(minutes=task.reminder_minutes)

    if reminder_time.tzinfo is None:
        reminder_time = reminder_time.replace(tzinfo=VIETNAM_TZ)

    now_vn = datetime.now(VIETNAM_TZ)

    if reminder_time <= now_vn:
        logger.info(f"Reminder time already passed for task {task.id}")
        return None

    result = send_reminder.apply_async(args=[task.id], eta=reminder_time)

    logger.info(f"Scheduled Celery task {result.id} for task {task.id} at {reminder_time}")

    return result.id


def cancel_reminder(task_id: int) -> bool:
    """Cancel a scheduled reminder for a task.

    Args:
        task_id: Task ID to cancel.

    Returns:
        True if cancelled, False otherwise.
    """
    from src.celery_app import celery_app

    celery_app.control.revoke(str(task_id), terminate=False)
    logger.info(f"Cancelled Celery task for task {task_id}")

    return True
