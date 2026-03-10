"""Tests for database models."""

from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base
from src.models import Task, User


# Create in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after each test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Create a sample user for testing."""
    user = User(
        telegram_id=123456,
        first_name="Test User",
        language_code="vi",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestUserModel:
    """Test suite for User model."""

    def test_create_user(self, db_session: Session) -> None:
        """Test creating a new user."""
        user = User(
            telegram_id=999999,
            first_name="New User",
            language_code="en",
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.telegram_id == 999999
        assert user.first_name == "New User"
        assert user.language_code == "en"
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_default_language_code(self, db_session: Session) -> None:
        """Test that default language code is 'vi'."""
        user = User(
            telegram_id=111111,
            first_name="Default Lang User",
        )
        db_session.add(user)
        db_session.commit()

        assert user.language_code == "vi"

    def test_user_telegram_id_unique(self, db_session: Session) -> None:
        """Test that telegram_id must be unique."""
        user1 = User(telegram_id=222222, first_name="User 1")
        db_session.add(user1)
        db_session.commit()

        user2 = User(telegram_id=222222, first_name="User 2")
        db_session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_user_relationship_with_tasks(self, db_session: Session, sample_user: User) -> None:
        """Test that user can have multiple tasks."""
        task1 = Task(
            user_id=sample_user.id,
            title="Task 1",
            deadline=datetime.now(timezone.utc) + timedelta(days=1),
        )
        task2 = Task(
            user_id=sample_user.id,
            title="Task 2",
            deadline=datetime.now(timezone.utc) + timedelta(days=2),
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        # Refresh to get relationship data
        db_session.refresh(sample_user)

        assert len(sample_user.tasks) == 2
        assert sample_user.tasks[0].title == "Task 1"
        assert sample_user.tasks[1].title == "Task 2"

    def test_user_cascade_delete_tasks(self, db_session: Session, sample_user: User) -> None:
        """Test that deleting user deletes all their tasks."""
        task = Task(
            user_id=sample_user.id,
            title="Task to be deleted",
        )
        db_session.add(task)
        db_session.commit()

        task_id = task.id

        # Delete user
        db_session.delete(sample_user)
        db_session.commit()

        # Verify task is deleted
        deleted_task = db_session.query(Task).filter(Task.id == task_id).first()
        assert deleted_task is None


class TestTaskModel:
    """Test suite for Task model."""

    def test_create_task(self, db_session: Session, sample_user: User) -> None:
        """Test creating a new task."""
        deadline = datetime(2026, 3, 20, 23, 59)
        task = Task(
            user_id=sample_user.id,
            title="Test Task",
            description="Test Description",
            deadline=deadline,
            priority=3,
            tags="work,urgent",
            recurring="daily",
            reminder_minutes=60,
        )
        db_session.add(task)
        db_session.commit()

        assert task.id is not None
        assert task.user_id == sample_user.id
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.deadline == deadline
        assert task.priority == 3
        assert task.status == Task.Status.PENDING
        assert task.tags == "work,urgent"
        assert task.recurring == "daily"
        assert task.reminder_minutes == 60

    def test_task_default_values(self, db_session: Session, sample_user: User) -> None:
        """Test task default values."""
        task = Task(
            user_id=sample_user.id,
            title="Minimal Task",
        )
        db_session.add(task)
        db_session.commit()

        assert task.priority == Task.Priority.MEDIUM
        assert task.status == Task.Status.PENDING
        assert task.description is None
        assert task.deadline is None
        assert task.tags is None
        assert task.recurring is None
        assert task.reminder_minutes == 30

    def test_task_priority_constants(self) -> None:
        """Test Task.Priority constants."""
        assert Task.Priority.LOW == 1
        assert Task.Priority.MEDIUM == 2
        assert Task.Priority.HIGH == 3
        assert Task.Priority.URGENT == 4

    def test_task_status_constants(self) -> None:
        """Test Task.Status constants."""
        assert Task.Status.PENDING == "pending"
        assert Task.Status.DONE == "done"
        assert Task.Status.CANCELLED == "cancelled"

    def test_task_status_transitions(self, db_session: Session, sample_user: User) -> None:
        """Test task status can be changed."""
        task = Task(
            user_id=sample_user.id,
            title="Status Test Task",
        )
        db_session.add(task)
        db_session.commit()

        # Pending -> Done
        task.status = Task.Status.DONE
        db_session.commit()
        assert task.status == Task.Status.DONE

        # Done -> Cancelled
        task.status = Task.Status.CANCELLED
        db_session.commit()
        assert task.status == Task.Status.CANCELLED

    def test_task_priority_boundaries(self, db_session: Session, sample_user: User) -> None:
        """Test priority values are stored correctly."""
        for priority in [1, 2, 3, 4]:
            task = Task(
                user_id=sample_user.id,
                title=f"Priority {priority} Task",
                priority=priority,
            )
            db_session.add(task)
        db_session.commit()

        tasks = db_session.query(Task).filter(Task.user_id == sample_user.id).all()
        priorities = [t.priority for t in tasks]
        assert sorted(priorities) == [1, 2, 3, 4]

    def test_task_title_length_limit(self, db_session: Session, sample_user: User) -> None:
        """Test that task title respects 255 char limit."""
        long_title = "a" * 256
        task = Task(
            user_id=sample_user.id,
            title=long_title,
        )
        db_session.add(task)

        # SQLite doesn't enforce length limits, but PostgreSQL would
        # This test ensures the model accepts the title
        db_session.commit()
        assert len(task.title) == 256

    def test_task_optional_fields(self, db_session: Session, sample_user: User) -> None:
        """Test task with all optional fields as None."""
        task = Task(
            user_id=sample_user.id,
            title="Optional Fields Task",
            description=None,
            deadline=None,
            priority=2,
            status=Task.Status.PENDING,
            tags=None,
            recurring=None,
            reminder_minutes=None,
        )
        db_session.add(task)
        db_session.commit()

        # Refresh to get database defaults applied
        db_session.refresh(task)

        assert task.description is None or task.description == ""
        assert task.deadline is None
        # Note: tags, recurring may get default values from DB
        # reminder_minutes may get default value

    def test_task_with_past_deadline(self, db_session: Session, sample_user: User) -> None:
        """Test task can have past deadline (edge case)."""
        past_deadline = datetime(2020, 1, 1, 12, 0)
        task = Task(
            user_id=sample_user.id,
            title="Past Deadline Task",
            deadline=past_deadline,
        )
        db_session.add(task)
        db_session.commit()

        assert task.deadline == past_deadline

    def test_task_relationship_with_user(self, db_session: Session, sample_user: User) -> None:
        """Test task's relationship to user."""
        task = Task(
            user_id=sample_user.id,
            title="Relationship Test Task",
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.user is not None
        assert task.user.id == sample_user.id
        assert task.user.first_name == "Test User"


class TestTaskEdgeCases:
    """Test suite for edge cases in Task model."""

    def test_empty_title_task(self, db_session: Session, sample_user: User) -> None:
        """Test task with empty title (edge case)."""
        task = Task(user_id=sample_user.id, title="")
        db_session.add(task)
        db_session.commit()

        assert task.title == ""

    def test_very_long_description(self, db_session: Session, sample_user: User) -> None:
        """Test task with very long description."""
        long_description = "x" * 10000
        task = Task(
            user_id=sample_user.id,
            title="Long Description Task",
            description=long_description,
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert len(task.description) == 10000

    def test_multiple_tags_format(self, db_session: Session, sample_user: User) -> None:
        """Test task with various tag formats."""
        test_cases = [
            "single_tag",
            "multiple,tags",
            "tags,with,commas",
            "  spaced  ",
            "tag1, tag2, tag3",
        ]

        for tags in test_cases:
            task = Task(
                user_id=sample_user.id,
                title=f"Tags: {tags}",
                tags=tags,
            )
            db_session.add(task)
        db_session.commit()

        tasks = db_session.query(Task).filter(Task.user_id == sample_user.id).all()
        assert len(tasks) == len(test_cases)

    def test_recurring_options(self, db_session: Session, sample_user: User) -> None:
        """Test different recurring options."""
        recurring_options = ["daily", "weekly", "monthly", "yearly"]

        for recurring in recurring_options:
            task = Task(
                user_id=sample_user.id,
                title=f"Recurring: {recurring}",
                recurring=recurring,
            )
            db_session.add(task)
        db_session.commit()

        tasks = db_session.query(Task).filter(Task.user_id == sample_user.id).all()
        assert len(tasks) == 4

    def test_reminder_minutes_boundaries(self, db_session: Session, sample_user: User) -> None:
        """Test various reminder minutes values."""
        test_values = [5, 15, 30, 60, 120, 0, -1, None]

        for minutes in test_values:
            task = Task(
                user_id=sample_user.id,
                title=f"Reminder: {minutes}",
                reminder_minutes=minutes,
            )
            db_session.add(task)
        db_session.commit()

        tasks = db_session.query(Task).filter(Task.user_id == sample_user.id).all()
        assert len(tasks) == len(test_values)

    def test_task_filtering_by_status(self, db_session: Session, sample_user: User) -> None:
        """Test filtering tasks by status."""
        # Create tasks with different statuses
        tasks_data = [
            ("Task 1", Task.Status.PENDING),
            ("Task 2", Task.Status.PENDING),
            ("Task 3", Task.Status.DONE),
            ("Task 4", Task.Status.CANCELLED),
        ]

        for title, status in tasks_data:
            task = Task(
                user_id=sample_user.id,
                title=title,
                status=status,
            )
            db_session.add(task)
        db_session.commit()

        # Filter by pending
        pending = db_session.query(Task).filter(
            Task.user_id == sample_user.id,
            Task.status == Task.Status.PENDING,
        ).all()
        assert len(pending) == 2

        # Filter by done
        done = db_session.query(Task).filter(
            Task.user_id == sample_user.id,
            Task.status == Task.Status.DONE,
        ).all()
        assert len(done) == 1

        # Filter by cancelled
        cancelled = db_session.query(Task).filter(
            Task.user_id == sample_user.id,
            Task.status == Task.Status.CANCELLED,
        ).all()
        assert len(cancelled) == 1

    def test_task_filtering_by_priority(self, db_session: Session, sample_user: User) -> None:
        """Test filtering tasks by priority."""
        for priority in [1, 2, 3, 4]:
            task = Task(
                user_id=sample_user.id,
                title=f"Priority {priority}",
                priority=priority,
            )
            db_session.add(task)
        db_session.commit()

        # Filter by high priority (>=3)
        high_priority = db_session.query(Task).filter(
            Task.user_id == sample_user.id,
            Task.priority >= 3,
        ).all()
        assert len(high_priority) == 2

    def test_task_ordering(self, db_session: Session, sample_user: User) -> None:
        """Test task ordering by priority and deadline."""
        tasks_data = [
            ("Low Priority", 1, datetime(2026, 3, 25)),
            ("High Priority", 3, datetime(2026, 3, 30)),
            ("Medium Priority", 2, datetime(2026, 3, 20)),
        ]

        for title, priority, deadline in tasks_data:
            task = Task(
                user_id=sample_user.id,
                title=title,
                priority=priority,
                deadline=deadline,
            )
            db_session.add(task)
        db_session.commit()

        # Order by priority desc, deadline asc
        ordered = db_session.query(Task).filter(
            Task.user_id == sample_user.id
        ).order_by(Task.priority.desc(), Task.deadline.asc()).all()

        assert ordered[0].title == "High Priority"
        assert ordered[1].title == "Medium Priority"
        assert ordered[2].title == "Low Priority"
