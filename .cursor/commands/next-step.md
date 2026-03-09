# Next Step

> Suggest the next action based on current project progress

## Purpose

This command analyzes the current progress and suggests what to do next. It reads `.docs/PROGRESS.md` to understand the current state.

## Workflow

### Step 1: Read Current Progress

Open and read `.docs/PROGRESS.md`:

1. Check "Current Status" table at the top
2. Identify which phase is marked as 🟡 In Progress
3. Look at "Next Steps" section
4. Check "Phase Details" for incomplete items

### Step 2: Analyze and Suggest

Based on the current phase, provide specific next steps:

#### If Phase 1 (Project Setup) is incomplete:
- Review `pyproject.toml` dependencies
- Check if `.env.example` exists
- Verify directory structure

#### If Phase 2 (Dependencies) is incomplete:
- Run `uv sync`
- Help create `.env` file
- Guide to set up PostgreSQL

#### If Phase 3 (Database Models) is incomplete:
- Create `src/models.py` with User, Task models
- Create `src/database.py` with connection logic
- Run `uv run alembic revision --autogenerate`

#### If Phase 4 (Bot Core) is incomplete:
- Create `src/main.py` with bot dispatcher
- Add basic handlers (start, help)
- Create `src/keyboard.py`

#### If Phase 5 (AI Agent) is incomplete:
- Create `src/agent.py` with LangChain
- Write system prompt
- Connect agent to bot handlers

#### If Phase 6 (Tools) is incomplete:
- Create LangChain tools in `src/tools.py`
- Implement add_task, list_tasks, update_task, delete_task
- Connect tools to agent

#### If Phase 7 (Scheduler) is incomplete:
- Create `src/scheduler.py`
- Set up APScheduler for reminders
- Implement notification logic

#### If Phase 8 (Tests) is incomplete:
- Create test files in `tests/`
- Write unit tests for models, tools, agent
- Run `uv run pytest`

### Step 3: Provide Actionable Output

Output should include:

1. **Current Phase**: Which phase is in progress
2. **Immediate Next Step**: One specific action to take
3. **Command to Run**: Actual command if applicable
4. **Files to Create/Modify**: Which files are involved
5. **Estimated Time**: Quick estimate (optional)

---

## Example Output

```
📍 Current Status: Phase 3 - Database Models (In Progress)

🎯 Next Step: Create database models

📝 Action Items:
1. Create `src/models.py` with User and Task models
2. Create `src/database.py` with SQLAlchemy setup
3. Run migration: uv run alembic revision --autogenerate -m "initial migration"

📂 Files to create/modify:
- src/models.py (new)
- src/database.py (new)
- alembic/versions/ (auto-generated)

💡 Tip: Follow the models defined in PROGRESS.md
```

---

## Quick Reference

| Current Phase | Suggested Next Action |
|---------------|----------------------|
| Phase 1 | Run `uv sync` to install dependencies |
| Phase 2 | Create `.env` and set up database |
| Phase 3 | Create `src/models.py` and `src/database.py` |
| Phase 4 | Create `src/main.py` with handlers |
| Phase 5 | Create `src/agent.py` |
| Phase 6 | Create `src/tools.py` |
| Phase 7 | Create `src/scheduler.py` |
| Phase 8 | Write tests in `tests/` |

---

## Important Notes

- Always read `.docs/PROGRESS.md` first
- Provide ONE clear next action, not everything at once
- Include actual commands the user can copy-paste
- Link to relevant documentation (SETUP.md, DEVELOPMENT.md)
- If all phases complete, suggest review/refinement

---

## Response Language

**IMPORTANT**: Always respond to the user in **Vietnamese** (tiếng Việt), even though this command file is in English.
