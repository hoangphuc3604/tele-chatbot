"""Scheduler for task reminders using Celery."""

import logging
from datetime import datetime, timezone, timedelta, date
from typing import Any, Optional

from src.database import SessionLocal
from src.models import Task, User, ImportantDate

logger = logging.getLogger(__name__)

VIETNAM_TZ = timezone(timedelta(hours=7))


class ReminderScheduler:
    """Scheduler for sending task reminders using Celery."""

    def __init__(self, bot: Any | None = None) -> None:
        """Initialize scheduler with optional bot instance."""
        self.bot = bot

    def set_bot(self, bot: Any) -> None:
        """Set bot instance for sending notifications."""
        self.bot = bot

    def _ensure_timezone(self, dt: datetime) -> datetime:
        """Ensure datetime has Vietnam timezone."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=VIETNAM_TZ)
        return dt.astimezone(VIETNAM_TZ)

    def schedule_reminder(self, task: Task) -> Optional[str]:
        """Schedule a reminder job for a task at exact time using Celery."""
        if not task.deadline:
            logger.info(f"Task {task.id} has no deadline")
            return None

        if task.reminder_minutes is None:
            logger.info(f"Task {task.id} has no reminder_minutes")
            return None

        from src.tasks import schedule_reminder as celery_schedule_reminder

        reminder_time = self._ensure_timezone(task.deadline)
        now_vn = datetime.now(VIETNAM_TZ)

        logger.info(f"Scheduling reminder for task {task.id}")
        logger.info(f"  Deadline: {task.deadline} -> {reminder_time}")
        logger.info(f"  Now (VN): {now_vn}")
        logger.info(f"  reminder_minutes: {task.reminder_minutes}")

        if reminder_time <= now_vn:
            logger.info(f"Reminder time already passed for task {task.id}")
            return None

        try:
            result = celery_schedule_reminder(task)
            logger.info(f"Scheduled Celery reminder for task {task.id}")
            return result
        except Exception as e:
            logger.error(f"Failed to schedule reminder for task {task.id}: {e}")
            return None

    def cancel_reminder(self, task_id: int) -> None:
        """Cancel a scheduled reminder for a task."""
        from src.tasks import cancel_reminder as celery_cancel_reminder

        try:
            celery_cancel_reminder(task_id)
            logger.info(f"Cancelled reminder for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to cancel reminder for task {task_id}: {e}")

    def schedule_important_date_reminder(self, important_date: ImportantDate) -> Optional[str]:
        """Schedule a reminder for an important date."""
        from src.holidays import convert_lunar_to_solar, get_vietnam_date
        from src.tasks import schedule_important_date_reminder as celery_schedule_date_reminder

        try:
            today = get_vietnam_date()
            target_date = self._calculate_next_date(important_date, today)

            if target_date is None:
                logger.info(f"No upcoming date found for important date {important_date.id}")
                return None

            reminder_date = target_date - timedelta(days=important_date.reminder_days_before)

            if reminder_date < today:
                next_target = self._calculate_next_date(important_date, reminder_date + timedelta(days=1))
                if next_target:
                    reminder_date = next_target - timedelta(days=important_date.reminder_days_before)
                else:
                    logger.info(f"Reminder date already passed for important date {important_date.id}")
                    return None

            result = celery_schedule_date_reminder(important_date.id, reminder_date)
            logger.info(f"Scheduled reminder for important date {important_date.id} on {reminder_date}")
            return result
        except Exception as e:
            logger.error(f"Failed to schedule reminder for important date {important_date.id}: {e}")
            return None

    def _calculate_next_date(self, important_date: ImportantDate, today) -> Optional[date]:
        """Calculate the next occurrence of an important date based on recurring type."""
        if important_date.recurring_type == ImportantDate.RecurringType.DAILY:
            return today
        elif important_date.recurring_type == ImportantDate.RecurringType.WEEKLY:
            return today + timedelta(days=7)
        elif important_date.recurring_type == ImportantDate.RecurringType.MONTHLY:
            return self._get_next_monthly_date(important_date.day, today)
        elif important_date.recurring_type == ImportantDate.RecurringType.YEARLY:
            return self._get_next_yearly_date(important_date.month, important_date.day, important_date.date_type, today)
        else:
            if important_date.date_type == ImportantDate.DateType.LUNAR:
                return convert_lunar_to_solar(important_date.month, important_date.day, today.year)
            else:
                return date(today.year, important_date.month, important_date.day)

    def _get_next_monthly_date(self, day: int, today) -> date:
        """Get next monthly date for a given day of month."""
        if today.day <= day:
            return date(today.year, today.month, day)
        else:
            if today.month == 12:
                return date(today.year + 1, 1, day)
            else:
                return date(today.year, today.month + 1, day)

    def _get_next_yearly_date(self, month: int, day: int, date_type: str, today) -> Optional[date]:
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

    def cancel_important_date_reminder(self, date_id: int) -> None:
        """Cancel a scheduled reminder for an important date."""
        from src.tasks import cancel_important_date_reminder as celery_cancel_date_reminder

        try:
            celery_cancel_date_reminder(date_id)
            logger.info(f"Cancelled reminder for important date {date_id}")
        except Exception as e:
            logger.error(f"Failed to cancel reminder for important date {date_id}: {e}")

    async def _send_reminder_job(self, task_id: int) -> None:
        """Job function to send reminder for a specific task (legacy)."""
        from src.tasks import send_reminder

        if not self.bot:
            logger.warning("Bot not set, cannot send reminder")
            return

        try:
            result = send_reminder(task_id)
            logger.info(f"Sent reminder for task {task_id}: {result}")
        except Exception as e:
            logger.error(f"Failed to send reminder for task {task_id}: {e}")

    async def start(self) -> None:
        """Start the scheduler (no-op for Celery)."""
        logger.info("Scheduler using Celery - no local scheduler needed")

    async def stop(self) -> None:
        """Stop the scheduler (no-op for Celery)."""
        logger.info("Scheduler stopped")


scheduler = ReminderScheduler()
