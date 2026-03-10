"""AI Agent for INKLIU Bot using LangChain."""

import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from src.tools import add_task, delete_task, delete_tasks, get_task, list_tasks, update_task

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
1. LUON TRA LOI BANG TIENG VIET CO DAU (vd: không, tôi, được, ngày, giờ)
2. Trả lời ngắn gọn, dễ đọc
3. KHONG DUNG QUA NHIU EMOJI - chi dung 1-2 emoji neu can thiet
4. Su dung format de dang doc: xuong dong cho moi muc

## Quy tắc quan trọng
- Khi người dùng yêu cầu thêm task, hãy gọi tool add_task
- Khi người dùng muốn xem danh sách, hãy gọi tool list_tasks
- Khi người dùng muốn xem chi tiết, hãy gọi tool get_task với task_id
- Khi người dùng muốn cập nhật, hãy gọi tool update_task
- Khi người dùng muốn xóa một task, hãy gọi tool delete_task
- Khi người dùng muốn xóa nhiều task, hãy gọi tool delete_tasks (với task_ids, status, hoặc delete_all)
- Nếu thiếu thông tin cần thiết (ví dụ: title khi thêm task), hãy hỏi người dùng

## Xử lý yêu cầu nhắc nhở (reminder)
Khi người dùng yêu cầu "nhắc tôi [việc] trong [thời gian]", bạn cần:
1. Tạo task mới với tiêu đề là việc cần nhắc
2. Tính deadline theo múi giờ Việt Nam (UTC+7)
   - Nếu là 23:44 hiện tại, "trong 1 phút" → deadline = 23:45
   - "trong 5 phút" → deadline = 23:49
   - "trong 1 giờ" → deadline = 00:44 (ngày mai)
3. Đặt reminder_minutes = 0 (nhắc đúng thời điểm deadline)

## Ví dụ phản hồi (tiếng Việt có dấu, không dùng nhiều emoji)
- "Đã thêm task: làm bài tập. Deadline: 23:00 10/03/2026"
- "Danh sách task của bạn: 1. làm bài tập (16:00 10/03), 2. đọc sách (18:00 10/03)"
- "Đã cập nhật task 1 thành done"
"""


def get_available_tools():
    """Return list of available tools."""
    return [add_task, list_tasks, get_task, update_task, delete_task, delete_tasks]


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

    # Ensure user exists in database and get database user ID
    db_user_id = get_or_create_user(user_id, first_name)

    try:
        agent = create_agent()

        # Get current date/time in Vietnam timezone
        VIETNAM_TZ = timezone(timedelta(hours=7))
        now = datetime.now(VIETNAM_TZ)
        current_date = now.strftime("%d/%m/%Y")
        current_time = now.strftime("%H:%M")

        # Build context with user info and current date/time - use database user ID for tools
        context = (
            f"Ngày hiện tại: {current_date}\n"
            f"Giờ hiện tại: {current_time}\n"
            f"Người dùng: {first_name} (Database ID: {db_user_id}, Telegram ID: {user_id})\n"
            f"QUAN TRONG: Tính deadline theo múi giờ Việt Nam (UTC+7)\n"
        )
        full_message = context + f"Tin nhắn: {message}"

        # Invoke agent with messages
        result = await agent.ainvoke({"messages": [HumanMessage(content=full_message)]})

        # Extract the last message (agent's response)
        messages = result.get("messages", [])
        if messages:
            response = messages[-1].content
            if isinstance(response, list):
                response = "".join(
                    block.get("text", "") for block in response if isinstance(block, dict)
                )
            return str(response)

        return "Xin lỗi, tôi không hiểu tin nhắn của bạn."

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return "❌ Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau."
