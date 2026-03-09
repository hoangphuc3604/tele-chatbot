"""Handlers package for INKLIU Bot."""

from aiogram import Dispatcher

from src.main import router


def register_handlers(dp: Dispatcher) -> None:
    """Register all handlers to dispatcher."""
    dp.include_router(router)
