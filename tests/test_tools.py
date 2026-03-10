"""Tests for LangChain tools - simplified version focusing on input schemas and basic validation."""

import pytest
from datetime import datetime


class TestToolInputSchemas:
    """Test suite for tool input schemas - these don't need database."""

    def test_add_task_input_defaults(self) -> None:
        """Test AddTaskInput default values."""
        from src.tools import AddTaskInput

        inp = AddTaskInput(user_id=1, title="Test")

        assert inp.description is None
        assert inp.deadline is None
        assert inp.priority == 2
        assert inp.tags is None
        assert inp.recurring is None
        assert inp.reminder_minutes == 30

    def test_add_task_input_with_all_fields(self) -> None:
        """Test AddTaskInput with all fields."""
        from src.tools import AddTaskInput

        deadline = datetime(2026, 3, 20, 23, 59)
        inp = AddTaskInput(
            user_id=1,
            title="Test Task",
            description="Description",
            deadline=deadline,
            priority=3,
            tags="work,urgent",
            recurring="daily",
            reminder_minutes=60,
        )

        assert inp.user_id == 1
        assert inp.title == "Test Task"
        assert inp.description == "Description"
        assert inp.deadline == deadline
        assert inp.priority == 3
        assert inp.tags == "work,urgent"
        assert inp.recurring == "daily"
        assert inp.reminder_minutes == 60

    def test_list_tasks_input_defaults(self) -> None:
        """Test ListTasksInput default values."""
        from src.tools import ListTasksInput

        inp = ListTasksInput(user_id=1)

        assert inp.status is None
        assert inp.priority is None
        assert inp.limit == 10

    def test_list_tasks_input_with_filters(self) -> None:
        """Test ListTasksInput with filters."""
        from src.tools import ListTasksInput

        inp = ListTasksInput(
            user_id=1,
            status="pending",
            priority=3,
            limit=20,
        )

        assert inp.user_id == 1
        assert inp.status == "pending"
        assert inp.priority == 3
        assert inp.limit == 20

    def test_update_task_input_defaults(self) -> None:
        """Test UpdateTaskInput default values."""
        from src.tools import UpdateTaskInput

        inp = UpdateTaskInput(task_id=1, user_id=1)

        assert inp.title is None
        assert inp.description is None
        assert inp.deadline is None
        assert inp.priority is None
        assert inp.status is None

    def test_delete_task_input(self) -> None:
        """Test DeleteTaskInput."""
        from src.tools import DeleteTaskInput

        inp = DeleteTaskInput(task_id=1, user_id=2)

        assert inp.task_id == 1
        assert inp.user_id == 2

    def test_get_task_input(self) -> None:
        """Test GetTaskInput."""
        from src.tools import GetTaskInput

        inp = GetTaskInput(task_id=1, user_id=2)

        assert inp.task_id == 1
        assert inp.user_id == 2


class TestToolsHaveDescriptions:
    """Test that tools have proper descriptions."""

    def test_add_task_has_description(self) -> None:
        """Test add_task has a description."""
        from src.tools import add_task
        assert add_task.description is not None
        assert len(add_task.description) > 0

    def test_list_tasks_has_description(self) -> None:
        """Test list_tasks has a description."""
        from src.tools import list_tasks
        assert list_tasks.description is not None
        assert len(list_tasks.description) > 0

    def test_get_task_has_description(self) -> None:
        """Test get_task has a description."""
        from src.tools import get_task
        assert get_task.description is not None
        assert len(get_task.description) > 0

    def test_update_task_has_description(self) -> None:
        """Test update_task has a description."""
        from src.tools import update_task
        assert update_task.description is not None
        assert len(update_task.description) > 0

    def test_delete_task_has_description(self) -> None:
        """Test delete_task has a description."""
        from src.tools import delete_task
        assert delete_task.description is not None
        assert len(delete_task.description) > 0


class TestToolNames:
    """Test that tools have correct names."""

    def test_tool_names_match_expected(self) -> None:
        """Test that tool names match expected format."""
        from src.tools import add_task, list_tasks, get_task, update_task, delete_task

        assert add_task.name == "add_task"
        assert list_tasks.name == "list_tasks"
        assert get_task.name == "get_task"
        assert update_task.name == "update_task"
        assert delete_task.name == "delete_task"


class TestGetOrCreateUser:
    """Test get_or_create_user function exists and is callable."""

    def test_function_exists(self) -> None:
        """Test get_or_create_user function exists."""
        from src.tools import get_or_create_user
        assert callable(get_or_create_user)


class TestSchedulerIntegration:
    """Test that scheduler is properly integrated."""

    def test_scheduler_exists(self) -> None:
        """Test scheduler module exists."""
        from src import scheduler
        assert scheduler is not None
        assert hasattr(scheduler, 'scheduler')

    def test_scheduler_has_reminder_methods(self) -> None:
        """Test scheduler has reminder methods."""
        from src.scheduler import scheduler
        assert hasattr(scheduler, 'schedule_reminder')
        assert hasattr(scheduler, 'cancel_reminder')
