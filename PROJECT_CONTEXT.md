# PROJECT_CONTEXT.md

## 1. Tổng quan dự án

- **Tên dự án**: INKLIU Bot (Personal Life Guardian)
- **Mục tiêu**: Người dùng chat tiếng Việt tự nhiên trong Telegram private chat. Bot dùng LangChain Agent (tool-calling) + Gemini để hiểu ý, tự chọn tool phù hợp, thực thi và trả lời.
- **Phong cách**: Giống ChatGPT + Todoist + Google Calendar kết hợp.
- **Phiên bản hiện tại**: Core + Inbox + Important Dates + Daily Brief (MVP).
- **Người dùng**: Multi-user (bạn + bạn bè), mỗi người có dữ liệu riêng hoàn toàn.

---

## 2. Công nghệ Stack

| Thành phần | Công nghệ |
|------------|-----------|
| Ngôn ngữ | Python 3.11+ |
| Telegram Bot | aiogram 3.x |
| AI/LLM | LangChain 0.3.x + Gemini 2.5 Flash |
| Database | PostgreSQL + SQLAlchemy 2.0 + Alembic |
| Scheduler | APScheduler 4.0+ với SQLAlchemyJobStore |
| Validation | Pydantic v2 |
| Env | python-dotenv, pydantic-settings |

---

## 3. Kiến trúc hệ thống

```
User (Telegram private chat) 
    ↓ (aiogram 3.x)
Telegram Handler → LangChain Agent Executor (per user)
    ↓ (tool calling)
Gemini 2.5 Flash (tool-calling native)
    ↓
Custom Tools (Pydantic @tool) 
    ↔ SQLAlchemy (PostgreSQL)
    ↔ APScheduler (BackgroundScheduler + SQLAlchemyJobStore)
```

- **Agent type**: `create_tool_calling_agent` (Gemini 2.5-flash hỗ trợ native function calling)
- **Memory**: `ConversationBufferWindowMemory` (k=10) + `EntityMemory` (riêng cho từng user)
- **Reminder engine**: APScheduler với `SQLAlchemyJobStore` (job lưu vào DB, survive restart)

---

## 4. Database Schema (SQLAlchemy models)

### User
- `id`: int (telegram user_id, primary key)
- `first_name`: str
- `timezone`: str = "Asia/Ho_Chi_Minh"
- `created_at`: datetime

### Task
- `id`: int (primary key)
- `user_id`: int (foreign key)
- `title`: str
- `deadline`: datetime
- `priority`: int (1-4)
- `tags`: JSON
- `recurring`: str (daily/weekly)
- `status`: str
- `created_at`: datetime

### ImportantDate
- `id`: int (primary key)
- `user_id`: int (foreign key)
- `title`: str
- `date`: date
- `remind_days_before`: JSON
- `note`: str

### InboxItem
- `id`: int (primary key)
- `user_id`: int (foreign key)
- `content`: text or url
- `category`: str (read/watch/reply)
- `added_at`: datetime
- `status`: str

---

## 5. Danh sách Tools cho LangChain Agent

Mỗi tool nhận thêm `user_id: int` để hỗ trợ multi-user.

1. `add_task(user_id, title, deadline, priority, tags, recurring)`
2. `list_tasks(user_id, filter)`
3. `mark_task_done(user_id, task_id)`
4. `snooze_task(user_id, task_id, minutes)`
5. `add_important_date(user_id, title, date, remind_before_days)`
6. `get_upcoming_dates(user_id, days)`
7. `add_to_inbox(user_id, content, category)`
8. `list_inbox(user_id, status)`
9. `mark_inbox_done(user_id, item_id)`
10. `generate_daily_brief(user_id)` → AI tóm tắt + gửi message
11. `create_pomodoro(user_id, minutes)`

---

## 6. System Prompt

```
Bạn là trợ lý cá nhân INKLIU của {first_name} (user_id: {user_id}).
Luôn trả lời ngắn gọn, vui vẻ, tiếng Việt.
Luôn confirm trước khi tạo task/date.
Ưu tiên gọi tool thay vì chỉ nói suông.
Nếu không hiểu → hỏi lại rõ ràng.
Chỉ xử lý dữ liệu của user này.
```

---

## 7. Chức năng theo Layer

### Layer 1 – Natural Language Core
- Chat tự nhiên tiếng Việt/Anh
- Bot confirm ngắn gọn + nút inline (Xác nhận / Sửa / Hủy)

### Layer 2 – Task & Deadline Management
- Thêm task: title, deadline, priority, tags, recurring, subtasks
- Xem: /today, /thisweek, /overdue, /all
- Mark done, snooze, delete
- Auto reminder: 24h, 1h, 10p trước

### Layer 3 – Important Dates
- Lưu ngày quan trọng: sinh nhật, kỷ niệm, lễ
- Nhắc trước 7 ngày, 3 ngày, 1 ngày + gợi ý quà (Gemini)

### Layer 4 – Inbox
- Forward link/ảnh/video/tin nhắn vào bot → tự lưu
- Phân loại: Read Later / Watch Later / Reply Later
- Daily Review buổi tối

### Layer 5 – Daily & Weekly Brief
- 8h sáng: deadline, inbox, sinh nhật
- 22h tối: task hoàn thành, inbox còn lại
- AI tóm tắt tuần

### Layer 6 – Pomodoro & Habit (thêm sau)
- /pomo 25 → đếm ngược
- Habit tracker đơn giản

---

## 8. Cấu trúc thư mục

```
inkliu_bot/
├── main.py              # aiogram + agent
├── agent.py             # LangChain agent setup
├── tools.py             # tất cả @tool
├── models.py            # SQLAlchemy models + Alembic
├── scheduler.py         # APScheduler
├── database.py
├── alembic/             # migration
└── .env
```

---

## 9. Environment Variables

```env
BOT_TOKEN=...
GOOGLE_API_KEY=...
DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname
```

---

## 10. Security & Privacy

- Mỗi user có dữ liệu hoàn toàn riêng (user_id = telegram user id)
- Bot tự tạo User record khi chat lần đầu
- API key Gemini trong `.env` (không commit)
