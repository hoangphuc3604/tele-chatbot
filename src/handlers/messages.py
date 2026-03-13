import logging
from aiogram import Router
from aiogram.types import Message

from src.agent import process_message


logger = logging.getLogger(__name__)
router = Router()


@router.message()
async def handle_message(message: Message) -> None:
    if not message.text:
        return

    if not message.from_user:
        return

    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    user_message = message.text

    logger.info(f"Message from {user_id}: {user_message}")

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        response = await process_message(user_id, user_message, first_name)
        if response:
            await message.answer(response, parse_mode="HTML")
        else:
            await message.answer("Xin lỗi, tôi không hiểu tin nhắn của bạn.")

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        error_msg = (
            "[Lỗi] Đã xảy ra lỗi khi xử lý tin nhắn của bạn.\n\n"
            "Vui lòng thử lại sau hoặc liên hệ hỗ trợ nếu lỗi tiếp tục xảy ra."
        )
        await message.answer(error_msg)
