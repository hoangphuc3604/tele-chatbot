"""Scheduler for task reminders using Celery."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from src.database import SessionLocal
from src.models import Task, User

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
