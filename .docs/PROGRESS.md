# INKLIU Bot - Project Progress

> Last updated: 2026-03-09

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
| AI Agent | ⚪ Not Started | No agent logic yet |
| Tools | ⚪ Not Started | No tools yet |
| Tests | ⚪ Not Started | No tests yet |

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

### ⚪ Phase 5: AI Agent

**Needs to be created:**

- [ ] `src/agent.py` - LangChain agent setup
- [ ] System prompt for agent

**Flow:**

```
User Message → Agent → Tool (if needed) → Response → User
```

### ⚪ Phase 6: Tools

**Needs to be created (LangChain tools):**

- [ ] `add_task` - Add new task
- [ ] `list_tasks` - List tasks
- [ ] `update_task` - Update task
- [ ] `delete_task` - Delete task
- [ ] `get_reminders` - Get reminders

### ⚪ Phase 7: Scheduler

**Needs to be created:**

- [ ] `src/scheduler.py` - APScheduler setup
- [ ] Reminder notifications

### ⚪ Phase 8: Tests

**Needs to be created:**

- [ ] `tests/test_models.py`
- [ ] `tests/test_tools.py`
- [ ] `tests/test_agent.py`

---

## Next Steps (Immediate Priority)

1. **Create AI agent**: `src/agent.py` with LangChain
2. **Create LangChain tools**: `src/tools.py` (add_task, list_tasks, etc.)
3. **Connect agent to bot**: Update handlers to use agent
4. **Set up scheduler**: `src/scheduler.py` for reminders

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
