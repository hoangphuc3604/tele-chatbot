"""Database models for INKLIU Bot."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class User(Base):
    """User model representing Telegram users."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    language_code: Mapped[Optional[str]] = mapped_column(String(10), default="vi")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="user", cascade="all, delete-orphan"
    )


class Task(Base):
    """Task model representing user tasks."""

    __tablename__ = "tasks"

    class Status:
        PENDING = "pending"
        DONE = "done"
        CANCELLED = "cancelled"

    class Priority:
        LOW = 1
        MEDIUM = 2
        HIGH = 3
        URGENT = 4

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    priority: Mapped[int] = mapped_column(Integer, default=Priority.MEDIUM)
    status: Mapped[str] = mapped_column(
        Enum(Status.PENDING, Status.DONE, Status.CANCELLED, name="task_status"),
        default=Status.PENDING,
    )
    tags: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    recurring: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="tasks")
