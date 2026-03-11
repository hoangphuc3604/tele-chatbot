"""Database models for INKLIU Bot."""

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class User(Base):
    """User model representing Telegram users."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    language_code: Mapped[Optional[str]] = mapped_column(String(10), default="vi")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="user", cascade="all, delete-orphan"
    )
    important_dates: Mapped[list["ImportantDate"]] = relationship(
        "ImportantDate", back_populates="user", cascade="all, delete-orphan"
    )
    conversation_history: Mapped[list["ConversationHistory"]] = relationship(
        "ConversationHistory", back_populates="user", cascade="all, delete-orphan"
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
    reminder_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=30)
    reminder_sent: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="tasks")


class ImportantDate(Base):
    """Important date model for birthdays, anniversaries, etc."""

    __tablename__ = "important_dates"

    class DateType:
        SOLAR = "solar"
        LUNAR = "lunar"

    class RecurringType:
        NONE = "none"
        DAILY = "daily"
        WEEKLY = "weekly"
        MONTHLY = "monthly"
        YEARLY = "yearly"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    date_type: Mapped[str] = mapped_column(String(10), default=DateType.LUNAR)
    month: Mapped[int] = mapped_column(Integer)
    day: Mapped[int] = mapped_column(Integer)
    year: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    reminder_days_before: Mapped[int] = mapped_column(Integer, default=3)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=True)
    recurring_type: Mapped[str] = mapped_column(String(20), default=RecurringType.YEARLY)
    last_reminder_sent: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(VIETNAM_TZ)
    )

    user: Mapped["User"] = relationship("User", back_populates="important_dates")


class ConversationHistory(Base):
    """Conversation history model for storing user chat history."""

    __tablename__ = "conversation_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(VIETNAM_TZ)
    )

    user: Mapped["User"] = relationship("User")
