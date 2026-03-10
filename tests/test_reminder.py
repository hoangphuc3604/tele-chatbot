"""Tests for reminder functionality in tasks.py and scheduler.py."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

from src.tasks import schedule_reminder, send_reminder
from src.scheduler import ReminderScheduler


VIETNAM_TZ = timezone(timedelta(hours=7))


class MockTask:
    """Mock Task object for testing."""

    def __init__(
        self,
        id: int = 1,
        user_id: int = 1,
        title: str = "Test Task",
        description: str | None = None,
        deadline: datetime | None = None,
        priority: int = 2,
        status: str = "pending",
        tags: str | None = None,
        recurring: str | None = None,
        reminder_minutes: int = 30,
    ):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.deadline = deadline
        self.priority = priority
        self.status = status
        self.tags = tags
        self.recurring = recurring
        self.reminder_minutes = reminder_minutes


class MockUser:
    """Mock User object for testing."""

    def __init__(self, id: int = 1, telegram_id: int = 123456, first_name: str = "Test"):
        self.id = id
        self.telegram_id = telegram_id
        self.first_name = first_name


class TestScheduleReminder:
    """Test suite for schedule_reminder function."""

    @patch("src.tasks.send_reminder")
    @patch("src.tasks.SessionLocal")
    def test_schedule_reminder_with_valid_deadline(self, mock_session_local, mock_send_reminder):
        """Test scheduling a reminder with valid future deadline."""
        # Setup
        future_deadline = datetime.now(VIETNAM_TZ) + timedelta(minutes=10)
        task = MockTask(id=1, deadline=future_deadline, reminder_minutes=5)

        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_result = MagicMock()
        mock_result.id = "celery-task-123"
        mock_send_reminder.apply_async.return_value = mock_result

        # Execute
        result = schedule_reminder(task)

        # Verify
        assert result == "celery-task-123"
        mock_send_reminder.apply_async.assert_called_once()

        call_args = mock_send_reminder.apply_async.call_args
        assert call_args[1]["args"] == [task.id]
        assert "eta" in call_args[1]

    @patch("src.tasks.send_reminder")
    def test_schedule_reminder_without_deadline(self, mock_send_reminder):
        """Test that reminder is not scheduled when deadline is None."""
        task = MockTask(id=1, deadline=None)

        result = schedule_reminder(task)

        assert result is None
        mock_send_reminder.apply_async.assert_not_called()

    @patch("src.tasks.send_reminder")
    def test_schedule_reminder_without_reminder_minutes(self, mock_send_reminder):
        """Test that reminder is not scheduled when reminder_minutes is None."""
        task = MockTask(id=1, reminder_minutes=None)

        result = schedule_reminder(task)

        assert result is None
        mock_send_reminder.apply_async.assert_not_called()

    @patch("src.tasks.send_reminder")
    def test_schedule_reminder_with_past_deadline(self, mock_send_reminder):
        """Test that reminder is not scheduled when deadline is in the past."""
        past_deadline = datetime.now(VIETNAM_TZ) - timedelta(minutes=10)
        task = MockTask(id=1, deadline=past_deadline, reminder_minutes=5)

        result = schedule_reminder(task)

        assert result is None
        mock_send_reminder.apply_async.assert_not_called()

    @patch("src.tasks.send_reminder")
    @patch("src.tasks.SessionLocal")
    def test_schedule_reminder_time_calculation(self, mock_session_local, mock_send_reminder):
        """Test that reminder time is correctly calculated as deadline - reminder_minutes."""
        # deadline = now + 60 minutes, reminder_minutes = 10
        # So reminder should be scheduled at now + 50 minutes
        deadline = datetime.now(VIETNAM_TZ) + timedelta(minutes=60)
        task = MockTask(id=1, deadline=deadline, reminder_minutes=10)

        mock_result = MagicMock()
        mock_result.id = "task-123"
        mock_send_reminder.apply_async.return_value = mock_result

        schedule_reminder(task)

        # Check that eta is deadline - reminder_minutes (60 - 10 = 50 minutes from now)
        call_args = mock_send_reminder.apply_async.call_args
        eta = call_args[1]["eta"]

        # The eta should be approximately deadline - reminder_minutes
        expected_eta = deadline - timedelta(minutes=10)
        assert abs((eta - expected_eta).total_seconds()) < 1


class TestSendReminder:
    """Test suite for send_reminder Celery task."""

    @patch("src.tasks.Bot")
    @patch("src.tasks.SessionLocal")
    def test_send_reminder_task_not_found(self, mock_session_local, mock_bot_class):
        """Test send_reminder when task doesn't exist."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = send_reminder(999)

        assert result == "Task 999 not found"
        mock_db.close.assert_called_once()

    @patch("src.tasks.Bot")
    @patch("src.tasks.SessionLocal")
    def test_send_reminder_task_not_pending(self, mock_session_local, mock_bot_class):
        """Test send_reminder when task status is not pending."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        task = MockTask(id=1, status="done")
        mock_db.query.return_value.filter.return_value.first.return_value = task

        result = send_reminder(1)

        assert result == "Task 1 is not pending"
        mock_db.close.assert_called_once()

    @patch("src.tasks.Bot")
    @patch("src.tasks.SessionLocal")
    def test_send_reminder_user_not_found(self, mock_session_local, mock_bot_class):
        """Test send_reminder when user doesn't exist."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        task = MockTask(id=1, user_id=999)
        mock_db.query.return_value.filter.return_value.first.side_effect = [task, None]

        result = send_reminder(1)

        assert "User not found" in result
        mock_db.close.assert_called_once()

    @patch("src.tasks.Bot")
    @patch("src.tasks.SessionLocal")
    def test_send_reminder_success(self, mock_session_local, mock_bot_class):
        """Test send_reminder generates correct message and calls bot."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot

        deadline = datetime(2026, 3, 15, 23, 0, tzinfo=VIETNAM_TZ)
        task = MockTask(
            id=1,
            user_id=1,
            title="Uống thuốc",
            description="Uống thuốc sau khi ăn",
            deadline=deadline,
            priority=3,
            status="pending",
        )
        user = MockUser(id=1, telegram_id=7772659580, first_name="User")

        mock_db.query.return_value.filter.return_value.first.side_effect = [task, user]

        result = send_reminder(1)

        assert "Reminder sent to user 7772659580" in result
        mock_bot.send_message.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("src.tasks.Bot")
    @patch("src.tasks.SessionLocal")
    def test_send_reminder_priority_emoji(self, mock_session_local, mock_bot_class):
        """Test send_reminder uses correct emoji for priority levels."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot

        task = MockTask(id=1, title="Task", priority=4, status="pending")
        user = MockUser(id=1)

        mock_db.query.return_value.filter.return_value.first.side_effect = [task, user]

        result = send_reminder(1)

        assert "Reminder sent to user" in result
        mock_bot.send_message.assert_called_once()


class TestReminderScheduler:
    """Test suite for ReminderScheduler class."""

    def test_ensure_timezone_with_tzinfo(self):
        """Test _ensure_timezone when datetime already has timezone."""
        scheduler = ReminderScheduler()

        dt = datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc)
        result = scheduler._ensure_timezone(dt)

        # Should convert from UTC to Vietnam timezone (+7)
        assert result.tzinfo is not None

    def test_ensure_timezone_without_tzinfo(self):
        """Test _ensure_timezone when datetime has no timezone."""
        scheduler = ReminderScheduler()

        dt = datetime(2026, 3, 15, 10, 0)
        result = scheduler._ensure_timezone(dt)

        # Should add Vietnam timezone
        assert result.tzinfo is not None

    @patch("src.tasks.schedule_reminder")
    def test_schedule_reminder_calls_celery(self, mock_celery_schedule):
        """Test that scheduler.schedule_reminder calls celery function."""
        scheduler = ReminderScheduler()

        future_deadline = datetime.now(VIETNAM_TZ) + timedelta(minutes=10)
        task = MockTask(id=1, deadline=future_deadline, reminder_minutes=5)

        mock_celery_schedule.return_value = "celery-task-id"

        result = scheduler.schedule_reminder(task)

        assert result == "celery-task-id"
        mock_celery_schedule.assert_called_once_with(task)

    @patch("src.tasks.schedule_reminder")
    def test_schedule_reminder_no_deadline(self, mock_celery_schedule):
        """Test that scheduler doesn't schedule when no deadline."""
        scheduler = ReminderScheduler()

        task = MockTask(id=1, deadline=None)

        result = scheduler.schedule_reminder(task)

        assert result is None
        mock_celery_schedule.assert_not_called()

    @patch("src.tasks.schedule_reminder")
    def test_schedule_reminder_past_deadline(self, mock_celery_schedule):
        """Test that scheduler doesn't schedule when deadline is in past."""
        scheduler = ReminderScheduler()

        past_deadline = datetime.now(VIETNAM_TZ) - timedelta(minutes=10)
        task = MockTask(id=1, deadline=past_deadline, reminder_minutes=5)

        result = scheduler.schedule_reminder(task)

        assert result is None
        mock_celery_schedule.assert_not_called()

    @patch("src.tasks.cancel_reminder")
    def test_cancel_reminder_calls_celery(self, mock_celery_cancel):
        """Test that cancel_reminder calls celery function."""
        scheduler = ReminderScheduler()

        scheduler.cancel_reminder(1)

        mock_celery_cancel.assert_called_once_with(1)


class TestReminderTimeCalculation:
    """Test suite for reminder time calculation edge cases."""

    def test_reminder_1_minute_before_deadline(self):
        """Test reminder is scheduled 1 minute before deadline."""
        with patch("src.tasks.send_reminder") as mock_task:
            deadline = datetime.now(VIETNAM_TZ) + timedelta(minutes=5)
            task = MockTask(id=1, deadline=deadline, reminder_minutes=1)

            mock_result = MagicMock()
            mock_result.id = "task-123"
            mock_task.apply_async.return_value = mock_result

            schedule_reminder(task)

            call_args = mock_task.apply_async.call_args
            eta = call_args[1]["eta"]

            # reminder_minutes = 1, so eta should be deadline - 1 minute
            expected_eta = deadline - timedelta(minutes=1)
            assert abs((eta - expected_eta).total_seconds()) < 1

    def test_reminder_with_large_priority_value(self):
        """Test reminder message uses correct emoji for high priority."""
        with patch("src.tasks.Bot") as mock_bot_class, \
             patch("src.tasks.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_bot = AsyncMock()
            mock_bot_class.return_value = mock_bot

            task = MockTask(id=1, title="Urgent Task", priority=4, status="pending")
            user = MockUser(id=1)

            mock_db.query.return_value.filter.return_value.first.side_effect = [task, user]

            result = send_reminder(1)

            assert "Reminder sent to user" in result

    def test_reminder_with_low_priority_value(self):
        """Test reminder message uses correct emoji for low priority."""
        with patch("src.tasks.Bot") as mock_bot_class, \
             patch("src.tasks.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_bot = AsyncMock()
            mock_bot_class.return_value = mock_bot

            task = MockTask(id=1, title="Low Priority", priority=1, status="pending")
            user = MockUser(id=1)

            mock_db.query.return_value.filter.return_value.first.side_effect = [task, user]

            result = send_reminder(1)

            assert "Reminder sent to user" in result
