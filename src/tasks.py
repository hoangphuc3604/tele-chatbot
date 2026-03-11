"""Celery tasks for INKLIU Bot."""

import logging
import os
from datetime import datetime, timezone, timedelta, date
from typing import Optional

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.celery_app import celery_app
from src.database import SessionLocal
from src.models import Task, User, ImportantDate
from src.holidays import convert_lunar_to_solar, get_vietnam_date

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

        if task.reminder_sent:
            logger.info(f"Reminder already sent for task {task_id}")
            return f"Reminder already sent for task {task_id}"

        user = db.query(User).filter(User.id == task.user_id).first()
        if not user:
            logger.warning(f"User not found for task {task_id}")
            return f"User not found for task {task_id}"

        priority_text = {
            1: "[Thấp]",
            2: "[TB]",
            3: "[Cao]",
            4: "[Khẩn]",
        }

        priority_mark = priority_text.get(task.priority, "[TB]")

        deadline_str = (
            task.deadline.strftime("%H:%M %d/%m/%Y") if task.deadline else ""
        )

        message = (
            f"<b>Nhắc nhở deadline!</b>\n\n"
            f"{priority_mark} <b>{task.title}</b>\n"
            f"Đến hạn: {deadline_str}\n"
        )

        if task.description:
            message += f"\n{task.description}"

        logger.info(f"Sending reminder for task {task.id} to user {user.telegram_id}")

        # Mark reminder as sent BEFORE sending to prevent duplicates
        # This is safe because we are in a transaction that will be committed
        # If sending fails, the retry will check again and re-send
        # But if the task crashes after this point but before commit,
        # we might lose the reminder.
        # A safer approach is to set this after successful send (see below).

        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            logger.error("BOT_TOKEN not found in environment")
            raise ValueError("BOT_TOKEN not configured")

        bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        import asyncio

        async def send_telegram_message():
            await bot.send_message(chat_id=user.telegram_id, text=message)

        asyncio.run(send_telegram_message())

        # Mark reminder as sent after successful Telegram API call
        task.reminder_sent = True
        db.commit()

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


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_important_date_reminder(self, date_id: int) -> str:
    """Send reminder for an important date to Telegram user.

    Args:
        date_id: Database important date ID.

    Returns:
        Confirmation message.
    """
    from datetime import timedelta
    db = SessionLocal()
    bot = None
    try:
        important_date = db.query(ImportantDate).filter(ImportantDate.id == date_id).first()

        if not important_date:
            logger.warning(f"Important date {date_id} not found")
            return f"Important date {date_id} not found"

        user = db.query(User).filter(User.id == important_date.user_id).first()
        if not user:
            logger.warning(f"User not found for important date {date_id}")
            return f"User not found for important date {date_id}"

        today = get_vietnam_date()
        current_datetime = datetime.now(VIETNAM_TZ)

        target_date = _calculate_next_date(important_date, today)

        if target_date is None:
            logger.info(f"No upcoming date found for important date {date_id}")
            return f"No upcoming date for important date {date_id}"

        days_until = (target_date - today).days

        date_type_text = "Âm lịch" if important_date.date_type == ImportantDate.DateType.LUNAR else "Dương lịch"
        recurring_text = _get_recurring_text(important_date.recurring_type)

        message = (
            f"<b>Nhắc nhở ngày quan trọng!</b>\n\n"
            f"<b>{important_date.title}</b>\n"
            f"Ngày: {important_date.day:02d}/{important_date.month:02d} ({date_type_text})\n"
            f"Loại: {recurring_text}\n"
            f"Còn {days_until} ngày nữa!\n"
        )

        if important_date.description:
            message += f"\n{important_date.description}"

        logger.info(f"Sending important date reminder for {important_date.id} to user {user.telegram_id}")

        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            logger.error("BOT_TOKEN not found in environment")
            raise ValueError("BOT_TOKEN not configured")

        bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

        import asyncio

        async def send_telegram_message():
            await bot.send_message(chat_id=user.telegram_id, text=message)

        asyncio.run(send_telegram_message())

        important_date.last_reminder_sent = current_datetime

        if important_date.recurring_type != ImportantDate.RecurringType.NONE:
            next_reminder_date = _calculate_next_reminder_date(important_date, target_date)
            if next_reminder_date:
                schedule_important_date_reminder(date_id, next_reminder_date)
                logger.info(f"Rescheduled next reminder for important date {date_id} on {next_reminder_date}")

        db.commit()

        logger.info(f"Important date reminder sent successfully for {important_date.id} to user {user.telegram_id}")

        return f"Important date reminder sent to user {user.telegram_id}"

    except Exception as e:
        logger.error(f"Failed to send important date reminder for {date_id}: {e}")
        raise self.retry(exc=e)
    finally:
        if bot:
            import asyncio
            asyncio.run(bot.session.close())
        db.close()


def _calculate_next_date(important_date: ImportantDate, today: date) -> Optional[date]:
    """Calculate the next occurrence of an important date."""
    if important_date.recurring_type == ImportantDate.RecurringType.DAILY:
        return today
    elif important_date.recurring_type == ImportantDate.RecurringType.WEEKLY:
        from datetime import timedelta
        return today + timedelta(days=7)
    elif important_date.recurring_type == ImportantDate.RecurringType.MONTHLY:
        return _get_next_monthly_date(important_date.day, today)
    elif important_date.recurring_type == ImportantDate.RecurringType.YEARLY:
        return _get_next_yearly_date(important_date.month, important_date.day, important_date.date_type, today)
    else:
        if important_date.date_type == ImportantDate.DateType.LUNAR:
            return convert_lunar_to_solar(important_date.month, important_date.day, today.year)
        else:
            return date(today.year, important_date.month, important_date.day)


def _get_next_monthly_date(day: int, today: date) -> date:
    """Get next monthly date for a given day of month."""
    if today.day <= day:
        return date(today.year, today.month, day)
    else:
        if today.month == 12:
            return date(today.year + 1, 1, day)
        else:
            return date(today.year, today.month + 1, day)


def _get_next_yearly_date(month: int, day: int, date_type: str, today: date) -> Optional[date]:
    """Get next yearly date."""
    if date_type == ImportantDate.DateType.LUNAR:
        target_date = convert_lunar_to_solar(month, day, today.year)
        if target_date < today:
            target_date = convert_lunar_to_solar(month, day, today.year + 1)
        return target_date
    else:
        target_date = date(today.year, month, day)
        if target_date < today:
            target_date = date(today.year + 1, month, day)
        return target_date


def _calculate_next_reminder_date(important_date: ImportantDate, target_date: date) -> Optional[date]:
    """Calculate the next reminder date based on recurring type."""
    reminder_date = target_date - timedelta(days=important_date.reminder_days_before)

    if reminder_date <= get_vietnam_date():
        next_target = _calculate_next_date(important_date, get_vietnam_date())
        if next_target:
            return next_target - timedelta(days=important_date.reminder_days_before)

    return reminder_date


def _get_recurring_text(recurring_type: str) -> str:
    """Get human-readable text for recurring type."""
    return {
        ImportantDate.RecurringType.DAILY: "Hàng ngày",
        ImportantDate.RecurringType.WEEKLY: "Hàng tuần",
        ImportantDate.RecurringType.MONTHLY: "Hàng tháng",
        ImportantDate.RecurringType.YEARLY: "Hàng năm",
        ImportantDate.RecurringType.NONE: "Một lần",
    }.get(recurring_type, "Một lần")


def schedule_important_date_reminder(date_id: int, reminder_date: date) -> Optional[str]:
    """Schedule a reminder for an important date using Celery.

    Args:
        date_id: Important date ID.
        reminder_date: Date to send reminder.

    Returns:
        Task ID or None if not scheduled.
    """
    reminder_datetime = datetime.combine(reminder_date, datetime.min.time())
    reminder_datetime = reminder_datetime.replace(hour=9, minute=0, tzinfo=VIETNAM_TZ)

    now_vn = datetime.now(VIETNAM_TZ)

    if reminder_datetime <= now_vn:
        logger.info(f"Reminder datetime already passed for important date {date_id}")
        return None

    result = send_important_date_reminder.apply_async(args=[date_id], eta=reminder_datetime)

    logger.info(f"Scheduled Celery task {result.id} for important date {date_id} at {reminder_datetime}")

    return result.id


def cancel_important_date_reminder(date_id: int) -> bool:
    """Cancel a scheduled reminder for an important date.

    Args:
        date_id: Important date ID to cancel.

    Returns:
        True if cancelled, False otherwise.
    """
    from src.celery_app import celery_app

    celery_app.control.revoke(str(date_id), terminate=False)
    logger.info(f"Cancelled Celery task for important date {date_id}")

    return True
