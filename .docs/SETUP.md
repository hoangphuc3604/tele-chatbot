# Setup Commands

> First-time setup guide for INKLIU Bot

## Prerequisites

- Python 3.12+
- PostgreSQL database (Railway, Neon, or local)
- Telegram Bot Token
- Google AI API Key

---

## 1. Install Dependencies

```bash
# Install all dependencies (including dev)
uv sync

# Or install dev group separately
uv sync --group dev
```

---

## 2. Environment Setup

```bash
# Copy environment template
copy env.example .env

# Or on Linux/Mac
cp env.example .env
```

Edit `.env` with your credentials:

```env
# Required
BOT_TOKEN=your_telegram_bot_token
GOOGLE_API_KEY=your_google_api_key
DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname

# Optional
# DEBUG=true
# REDIS_URL=redis://localhost:6379/0
```

---

## 3. Database Setup

### Option A: Local PostgreSQL

```bash
# Create database
createdb inkliu_bot

# Update DATABASE_URL in .env
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/inkliu_bot
```

### Option B: Railway/Neon

1. Create project on [Railway](https://railway.app/) or [Neon](https://neon.tech/)
2. Get connection string
3. Update DATABASE_URL in .env

---

## 4. Initialize Alembic

```bash
# Create initial migration
uv run alembic revision --autogenerate -m "initial migration"

# Apply migrations
uv run alembic upgrade head
```

---

## 5. Run the Bot

```bash
# Development mode
uv run python -m src.main

# Or with debug
uv run python -m src.main --debug
```

---

## 6. Verify Installation

```bash
# Check installed packages
uv pip list

# Run tests
uv run pytest

# Check linting
uv run ruff check src/
```

---

## Troubleshooting

### Module not found

```bash
# Reinstall dependencies
uv sync
```

### Database connection error

- Check DATABASE_URL in `.env`
- Verify PostgreSQL is running
- Check firewall/network settings

### Bot not responding

- Check BOT_TOKEN is correct
- Verify bot is started via @BotFather
- Check logs for errors
