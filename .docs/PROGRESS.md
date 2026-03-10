# INKLIU Bot - Project Progress

> Last updated: 2026-03-10

## Project Overview

- **Project Name**: INKLIU Bot (Telegram Personal Assistant)
- **Type**: Telegram Bot with AI Agent
- **Target Users**: Vietnamese users (also supports English)
- **Tech Stack**: Python 3.12+, aiogram 3.x, LangChain, SQLAlchemy, PostgreSQL

---

## Current Status

| Phase | Status | Notes |
|-------|--------|-------|
| Project Setup | ✅ Completed | Basic structure established |
| Dependencies | ✅ Completed | Installed via uv sync |
| Database | ✅ Completed | Models created, migration applied |
| Bot Core | ✅ Completed | Basic handlers created |
| AI Agent | ✅ Completed | LangChain agent created |
| Tools | ✅ Completed | Task management tools |
| Tests | ✅ Completed | 59 tests passing |

---

## Phase Details

### ✅ Phase 1: Project Setup (Completed)

- [x] Create `pyproject.toml` with dependencies
- [x] Set up `.cursor/rules/inkliu-bot.mdc` (project rules)
- [x] Set up `.gitignore`
- [x] Create directory structure `src/` and `tests/`
- [x] Create `env.example` template

### ✅ Phase 2: Dependencies (Completed)

**Completed:**

- [x] Install core dependencies: `uv sync`
- [x] Install dev dependencies: `uv sync --group dev`
- [x] Create `.env` (copy from `env.example`)
- [x] PostgreSQL database configured

### ✅ Phase 3: Database Models (Completed)

**Completed:**

- [x] `src/models.py` - SQLAlchemy models (User, Task)
- [x] `src/database.py` - Database connection & session
- [x] Alembic migrations applied

**Expected models:**

```
User
├── id (PK)
├── telegram_id (unique)
├── first_name
├── created_at
└── updated_at

Task
├── id (PK)
├── user_id (FK → User)
├── title
├── description
├── deadline
├── priority
├── status (pending/done)
├── tags
├── recurring
├── created_at
└── updated_at
```

### ✅ Phase 4: Bot Core (Completed)

**Completed:**

- [x] `src/main.py` - Bot entry point, dispatcher setup
- [x] `src/keyboard.py` - Inline keyboards
- [x] `src/handlers/` - Basic handlers (/start, /help)

### ✅ Phase 5: AI Agent (Completed)

**Completed:**

- [x] `src/agent.py` - LangChain agent setup với Gemini
- [x] System prompt cho agent
- [x] Kết nối agent với bot handlers

### ✅ Phase 6: Tools (Completed)

**Completed (LangChain tools):**

- [x] `add_task` - Thêm task mới
- [x] `list_tasks` - Liệt kê task
- [x] `get_task` - Xem chi tiết task
- [x] `update_task` - Cập nhật task
- [x] `delete_task` - Xóa task

### ✅ Phase 7: Scheduler (Completed)

**Completed:**

- [x] `src/scheduler.py` - APScheduler setup
- [x] Reminder notifications (60, 30, 15 minutes before deadline)

### ✅ Phase 8: Tests (Completed)

**Completed:**

- [x] `tests/test_models.py` - Model tests (21 tests)
- [x] `tests/test_tools.py` - Tool input schema tests (18 tests)
- [x] `tests/test_agent.py` - Agent tests (20 tests)

**Test Results:** 59 tests passing

---

## Next Steps (Immediate Priority)

1. **Set up Google API Key**: Thêm `GOOGLE_API_KEY` vào `.env`
2. **Test bot**: Chạy `uv run python -m src.main` và chat thử
3. **Run tests**: `uv run pytest tests/ -v`

---

## Notes for AI Agent

- Read `.cursor/rules/inkliu-bot.mdc` before coding
- Follow code style: 4 spaces, type hints, PEP8 imports
- Don't edit `pyproject.toml` directly → use `uv add`
- Use async/await with aiogram 3.x
- Write tests when implementing features

---

## User Language Support

- **Primary**: Vietnamese (tiếng Việt)
- **Secondary**: English (tiếng Anh)
- Bot responses should be in Vietnamese by default, but can detect user language preference

---

## Resources

- [aiogram docs](https://docs.aiogram.dev/)
- [LangChain docs](https://python.langchain.com/)
- [SQLAlchemy docs](https://docs.sqlalchemy.org/)
- [Google AI Studio](https://aistudio.google.com/app/apikey)
