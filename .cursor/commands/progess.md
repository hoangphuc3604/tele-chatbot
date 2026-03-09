# Progress Tracker

> Track and update project progress based on current codebase state

## Purpose

This command helps the agent understand the current state of the project and update `.docs/PROGRESS.md` accordingly.

## Workflow

### Step 1: Analyze Current Codebase

Read the following files to understand the current project state:

1. **Check main entry point**: `main.py` - What's implemented?
2. **Check src/ directory**: What modules exist?
   - `src/__init__.py`
   - `src/models.py` (if exists)
   - `src/database.py` (if exists)
   - `src/agent.py` (if exists)
   - `src/tools.py` (if exists)
   - `src/keyboard.py` (if exists)
   - `src/scheduler.py` (if exists)
   - `src/main.py` (if exists)
3. **Check tests/ directory**: What tests exist?
4. **Check pyproject.toml**: What dependencies are declared?
5. **Check alembic/**: Any migrations exist?

### Step 2: Determine Current Phase

Based on the codebase analysis, determine which phase the project is in:

| Phase | Indicator |
|-------|-----------|
| Phase 1: Project Setup | `pyproject.toml`, `.cursor/rules/`, `env.example` exist |
| Phase 2: Dependencies | `.env` exists, `uv sync` has been run |
| Phase 3: Database Models | `src/models.py`, `src/database.py` exist, migrations exist |
| Phase 4: Bot Core | `src/main.py` with handlers, `src/keyboard.py` |
| Phase 5: AI Agent | `src/agent.py` with LangChain setup |
| Phase 6: Tools | LangChain tools in `src/tools.py` |
| Phase 7: Scheduler | `src/scheduler.py` with APScheduler |
| Phase 8: Tests | Test files in `tests/` directory |

### Step 3: Update PROGRESS.md

Follow `.docs/UPDATE-PROGRESS.md` guidelines:

1. Open `.docs/PROGRESS.md`
2. Update "Current Status" table:
   - Mark completed phases as ✅
   - Mark current phase as 🟡 In Progress
   - Mark future phases as ⚪ Not Started
3. Update "Phase Details" section with checkmarks for completed items
4. Update "Next Steps" to reflect upcoming work

### Step 4: Commit Changes

```bash
git add .docs/PROGRESS.md
git commit -m "docs: update project progress"
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| Analyze codebase | List files in `src/`, `tests/`, check `pyproject.toml` |
| Check dependencies | Look for `.env` file |
| Check database | Look for `alembic/versions/` migrations |
| Check bot | Look for handlers in `src/` |
| Update progress | Edit `.docs/PROGRESS.md` |

---

## Important Notes

- Always read the actual codebase files before updating progress
- Don't assume - verify by checking if files exist
- Mark previous phases as ✅ when they're done
- Keep "Next Steps" updated with immediate priorities
- Include brief notes about what was completed

---

## Response Language

**IMPORTANT**: Always respond to the user in **Vietnamese** (tiếng Việt), even though this command file is in English.
