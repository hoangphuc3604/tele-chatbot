# INKLIU Bot

Telegram personal assistant bot with AI-powered task management using LangChain and Gemini.

## Features

- Natural language task management in Vietnamese or English
- Add, list, update, and delete tasks with priorities and deadlines
- Multi-user support (each user has their own private data)
- AI-powered responses using Gemini 2.5 Flash

## Prerequisites

- Python 3.12+
- PostgreSQL (or use Docker)
- Telegram Bot Token
- Google AI API Key

## Quick Start

### 1. Clone and Setup

```bash
cd telegram-bot
```

### 2. Create Virtual Environment

```bash
uv venv
uv sync
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```
BOT_TOKEN=your_telegram_bot_token
GOOGLE_API_KEY=your_google_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/tele_chatbot
```

### 4. Run Database Migrations

```bash
uv run alembic upgrade head
```

### 5. Start the Bot

```bash
uv run python -m src.main
```

## Using Docker

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```
BOT_TOKEN=your_telegram_bot_token
GOOGLE_API_KEY=your_google_api_key
DATABASE_URL=postgresql://root:root@postgres:5432/tele_chatbot
```

### 2. Build and Run

```bash
docker-compose up --build
```

### 3. Run Migrations

```bash
docker-compose exec bot uv run alembic upgrade head
```

## Bot Commands

- `/start` - Start the bot
- `/help` - Show help message
- Just send a message in natural language to interact

## Example Usage

```
You: Thêm task làm bài tập toán ngày mai 23h
Bot: ✅ Đã thêm task mới!
     📝 làm bài tập toán
     ⏰ Deadline: 11/03/2026 23:00
     🔢 Priority: trung bình
     🆔 Task ID: 1

You: Liệt kê các task của tôi
Bot: 📋 Danh sách công việc:
     1. ⏳ làm bài tập toán
        🆔 ID: 1 | 🟡 Priority 2 | ⏰ 11/03/2026 23:00
```

## Project Structure

```
telegram-bot/
├── src/
│   ├── main.py        # Bot entry point
│   ├── agent.py       # LangChain agent setup
│   ├── tools.py       # Custom tools for agent
│   ├── models.py      # SQLAlchemy models
│   ├── database.py    # Database connection
│   └── keyboard.py    # Telegram keyboards
├── alembic/           # Database migrations
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Technology Stack

- **Bot Framework**: aiogram 3.x
- **AI**: LangChain + Gemini 2.5 Flash
- **Database**: PostgreSQL + SQLAlchemy 2.0
- **Migrations**: Alembic

## License

MIT
