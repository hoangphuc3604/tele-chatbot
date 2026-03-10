"""Celery application configuration."""

from celery import Celery

celery_app = Celery(
    "inkliu_bot",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

# Import tasks to register them with the worker
from src import tasks  # noqa: F401

celery_app.conf.update(
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=False,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    beat_schedule={},
)
