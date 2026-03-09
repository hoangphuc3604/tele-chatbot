"""AI Agent for INKLIU Bot using LangChain."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from src.tools import add_task, delete_task, get_task, list_tasks, update_task

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là INKLIU Bot - Trợ lý AI cá nhân cho người dùng Telegram.

## Nhiệm vụ
Bạn giúp người dùng quản lý công việc (tasks) bằng cách:
- Thêm task mới
- Liệt kê các task hiện có
- Xem chi tiết một task
- Cập nhật task
- Xóa task

## Cách phản hồi
1. Luôn trả lời bằng tiếng Việt
2. Trả lời ngắn gọn, thân thiện
3. Sử dụng emoji để trả lời sinh động hơn
4. Khi có kết quả từ tool, tóm tắt ngắn gọn cho người dùng

## Quy tắc quan trọng
- Khi người dùng yêu cầu thêm task, hãy gọi tool add_task
- Khi người dùng muốn xem danh sách, hãy gọi tool list_tasks
- Khi người dùng muốn xem chi tiết, hãy gọi tool get_task với task_id
- Khi người dùng muốn cập nhật, hãy gọi tool update_task
- Khi người dùng muốn xóa, hãy gọi tool delete_task
- Nếu thiếu thông tin cần thiết (ví dụ: title khi thêm task), hãy hỏi người dùng

## Ví dụ
- Người dùng: "thêm task làm bài tập" → Gọi add_task(title="làm bài tập")
- Người dùng: "xem task của tôi" → Gọi list_tasks
- Người dùng: "task 1 đã xong" → Gọi update_task(task_id=1, status="done")
"""


def get_available_tools():
    """Return list of available tools."""
    return [add_task, list_tasks, get_task, update_task, delete_task]


def create_agent():
    """Create and return LangChain agent with tools."""
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        max_tokens=1024,
        api_key=google_api_key,
    )

    tools = get_available_tools()

    # Create agent using the new LangChain 0.3+ API
    from langchain.agents import create_agent

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    return agent


async def process_message(user_id: int, message: str, first_name: str) -> str:
    """Process user message and return agent response.

    Args:
        user_id: Telegram user ID.
        message: User's message.
        first_name: User's first name.

    Returns:
        Agent's response as string.
    """
    from src.tools import get_or_create_user

    # Ensure user exists in database
    user = get_or_create_user(user_id, first_name)

    try:
        agent = create_agent()

        # Build context with user info
        context = f"Người dùng: {first_name} (ID: {user_id})\n"
        full_message = context + f"Tin nhắn: {message}"

        # Invoke agent with messages
        result = await agent.ainvoke({"messages": [HumanMessage(content=full_message)]})

        # Extract the last message (agent's response)
        messages = result.get("messages", [])
        if messages:
            response = messages[-1].content
            return response

        return "Xin lỗi, tôi không hiểu tin nhắn của bạn."

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return f"❌ Đã xảy ra lỗi: {str(e)}. Vui lòng thử lại sau."
