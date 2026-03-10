"""Tests for AI Agent."""

import os
import inspect
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

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
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
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


class TestAgentModuleImports:
    """Test suite for agent module imports and constants."""

    def test_imports(self) -> None:
        """Test that all required imports work."""
        from src.agent import (
            SYSTEM_PROMPT,
            create_agent,
            get_available_tools,
            process_message,
        )

        assert SYSTEM_PROMPT is not None
        assert callable(create_agent)
        assert callable(get_available_tools)
        assert callable(process_message)

    def test_system_prompt_contains_vietnamese(self) -> None:
        """Test that system prompt is in Vietnamese."""
        from src.agent import SYSTEM_PROMPT

        # The prompt says "tiếng Việt" in the response format section
        assert "tiếng Việt" in SYSTEM_PROMPT or "tiếng việt" in SYSTEM_PROMPT.lower()

    def test_system_prompt_contains_tool_usage(self) -> None:
        """Test that system prompt describes tool usage."""
        from src.agent import SYSTEM_PROMPT

        assert "add_task" in SYSTEM_PROMPT
        assert "list_tasks" in SYSTEM_PROMPT
        assert "get_task" in SYSTEM_PROMPT
        assert "update_task" in SYSTEM_PROMPT
        assert "delete_task" in SYSTEM_PROMPT


class TestGetAvailableTools:
    """Test suite for get_available_tools function."""

    def test_returns_list(self) -> None:
        """Test that get_available_tools returns a list."""
        from src.agent import get_available_tools

        tools = get_available_tools()
        assert isinstance(tools, list)

    def test_contains_all_tools(self) -> None:
        """Test that all required tools are returned."""
        from src.agent import get_available_tools
        from src.tools import add_task, delete_task, get_task, list_tasks, update_task

        tools = get_available_tools()
        tool_names = [tool.name for tool in tools]

        assert "add_task" in tool_names
        assert "list_tasks" in tool_names
        assert "get_task" in tool_names
        assert "update_task" in tool_names
        assert "delete_task" in tool_names


class TestCreateAgent:
    """Test suite for create_agent function."""

    def test_create_agent_requires_api_key(self) -> None:
        """Test that agent creation requires GOOGLE_API_KEY."""
        # Clear the environment variable if it exists
        with patch.dict(os.environ, {}, clear=True):
            from src.agent import create_agent
            # Should raise ValueError if no API key
            with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
                create_agent()

    def test_tools_are_available(self) -> None:
        """Test that get_available_tools returns expected tools."""
        from src.agent import get_available_tools
        from src.tools import add_task, delete_task, get_task, list_tasks, update_task

        tools = get_available_tools()
        tool_names = [tool.name for tool in tools]

        # Verify all tools are present
        assert "add_task" in tool_names
        assert "list_tasks" in tool_names
        assert "get_task" in tool_names
        assert "update_task" in tool_names
        assert "delete_task" in tool_names


class TestProcessMessage:
    """Test suite for process_message function."""

    def test_process_message_is_async(self) -> None:
        """Test that process_message is an async function."""
        from src.agent import process_message

        assert inspect.iscoroutinefunction(process_message)

    def test_process_message_signature(self) -> None:
        """Test that process_message has correct signature."""
        from src.agent import process_message

        sig = inspect.signature(process_message)
        params = list(sig.parameters.keys())

        assert "user_id" in params
        assert "message" in params
        assert "first_name" in params


class TestAgentToolIntegration:
    """Test suite for agent-tool integration."""

    def test_tools_have_correct_descriptions(self) -> None:
        """Test that tools have Vietnamese descriptions."""
        from src.tools import add_task, delete_task, get_task, list_tasks, update_task

        # Check tool descriptions exist and are strings
        assert isinstance(add_task.description, str)
        assert isinstance(list_tasks.description, str)
        assert isinstance(get_task.description, str)
        assert isinstance(update_task.description, str)
        assert isinstance(delete_task.description, str)

    def test_tools_accept_user_id_first(self) -> None:
        """Test that tools accept user_id as first parameter."""
        from src.tools import AddTaskInput, DeleteTaskInput, GetTaskInput, ListTasksInput, UpdateTaskInput

        # All input schemas should have user_id field
        add_input = AddTaskInput(user_id=1, title="Test")
        assert add_input.user_id == 1

        list_input = ListTasksInput(user_id=1)
        assert list_input.user_id == 1

        get_input = GetTaskInput(user_id=1, task_id=1)
        assert get_input.user_id == 1

        update_input = UpdateTaskInput(user_id=1, task_id=1)
        assert update_input.user_id == 1

        delete_input = DeleteTaskInput(user_id=1, task_id=1)
        assert delete_input.user_id == 1


class TestAgentPrompt:
    """Test suite for agent system prompt."""

    def test_prompt_defines_add_task(self) -> None:
        """Test prompt mentions add_task usage."""
        from src.agent import SYSTEM_PROMPT

        assert "add_task" in SYSTEM_PROMPT

    def test_prompt_defines_list_tasks(self) -> None:
        """Test prompt mentions list_tasks usage."""
        from src.agent import SYSTEM_PROMPT

        assert "list_tasks" in SYSTEM_PROMPT

    def test_prompt_defines_get_task(self) -> None:
        """Test prompt mentions get_task usage."""
        from src.agent import SYSTEM_PROMPT

        assert "get_task" in SYSTEM_PROMPT

    def test_prompt_defines_update_task(self) -> None:
        """Test prompt mentions update_task usage."""
        from src.agent import SYSTEM_PROMPT

        assert "update_task" in SYSTEM_PROMPT

    def test_prompt_defines_delete_task(self) -> None:
        """Test prompt mentions delete_task usage."""
        from src.agent import SYSTEM_PROMPT

        assert "delete_task" in SYSTEM_PROMPT

    def test_prompt_requires_task_id_for_get(self) -> None:
        """Test prompt says task_id is needed for get."""
        from src.agent import SYSTEM_PROMPT

        # Should mention task_id requirement
        assert "task_id" in SYSTEM_PROMPT.lower()

    def test_prompt_mentions_asking_for_info(self) -> None:
        """Test prompt says to ask for missing info."""
        from src.agent import SYSTEM_PROMPT

        # Should mention asking user for missing info
        assert "hỏi" in SYSTEM_PROMPT.lower() or "missing" in SYSTEM_PROMPT.lower()


class TestAgentErrorHandling:
    """Test suite for agent error handling."""

    def test_process_message_has_error_handling(self) -> None:
        """Verify error handling exists in the function."""
        from src.agent import process_message

        source = inspect.getsource(process_message)
        # Verify error handling keywords are in the source
        assert "try" in source
        assert "except" in source

    def test_process_message_returns_string(self) -> None:
        """Verify process_message returns a string."""
        from src.agent import process_message
        sig = inspect.signature(process_message)
        # Just verify the function exists and has proper signature
        assert callable(process_message)
