from aiogram import Dispatcher

from src.handlers.commands import router as commands_router
from src.handlers.tasks import router as tasks_router
from src.handlers.messages import router as messages_router


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(commands_router)
    dp.include_router(tasks_router)
    dp.include_router(messages_router)
