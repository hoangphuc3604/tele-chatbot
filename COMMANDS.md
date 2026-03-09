# Development Commands

## Package Management (uv)

| Command | Mô tả |
|---------|-------|
| `uv sync` | Install/update dependencies từ pyproject.toml |
| `uv add <package>` | Thêm package mới và cập nhật pyproject.toml |
| `uv add --dev <package>` | Thêm dev dependency |
| `uv remove <package>` | Xóa package |
| `uv pip list` | List tất cả packages đã installed |
| `uv venv` | Tạo virtual environment |

---

## Run Bot

| Command | Mô tả |
|---------|-------|
| `uv run python -m src.main` | Chạy bot (sử dụng uv run để dùng đúng environment) |
| `uv run python -m src.main --debug` | Chạy bot ở debug mode |

---

## Database (Alembic)

| Command | Mô tả |
|---------|-------|
| `uv run alembic init alembic` | Khởi tạo Alembic (chỉ chạy 1 lần) |
| `uv run alembic revision --autogenerate -m "migration message"` | Tạo migration mới |
| `uv run alembic upgrade head` | Apply tất cả migrations |
| `uv run alembic upgrade +1` | Apply 1 migration tiếp theo |
| `uv run alembic downgrade -1` | Rollback 1 migration |
| `uv run alembic current` | Xem migration hiện tại |
| `uv run alembic history` | Xem lịch sử migrations |
| `uv run alembic check` | Kiểm tra xem có migration mới không |

---

## Testing (pytest)

| Command | Mô tả |
|---------|-------|
| `uv run pytest` | Chạy tất cả tests |
| `uv run pytest tests/` | Chạy tests trong folder tests/ |
| `uv run pytest tests/test_tools.py` | Chạy 1 file test |
| `uv run pytest -v` | Chạy tests với verbose output |
| `uv run pytest -k "test_add"` | Chạy tests có tên chứa "test_add" |
| `uv run pytest --cov=src` | Chạy tests với coverage report |
| `uv run pytest --cov=src --cov-report=html` | Coverage report dạng HTML |

---

## Linting & Formatting

| Command | Mô tả |
|---------|-------|
| `uv run ruff check src/` | Check linting errors |
| `uv run ruff check src/ --fix` | Auto-fix linting errors |
| `uv run ruff format src/` | Format code |
| `uv run mypy src/` | Type checking với mypy |

---

## Development Helpers

| Command | Mô tả |
|---------|-------|
| `uv run python -c "from src.models import Base; Base.metadata.create_all()"` | Tạo tables (dev only) |
| `uv run python -m src.scheduler` | Chạy scheduler riêng (nếu cần) |

---

## Git Commands

| Command | Mô tả |
|---------|-------|
| `git checkout -b feature/<tên-feature>` | Tạo branch mới |
| `git checkout -b bugfix/<tên-bug>` | Tạo branch fix bug |
| `git commit -m "feat: add new feature"` | Commit theo conventional commits |
| `git commit -m "fix: fix bug in task"` | Commit fix bug |

### Conventional Commits Format
```
<type>: <mô tả ngắn>

[optional body]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation
- `test`: Testing
- `chore`: Maintenance

---

## Environment Setup (First Time)

```bash
# 1. Clone repo và cd vào
cd telegram-bot

# 2. Tạo virtual environment với uv
uv venv

# 3. Install dependencies
uv sync

# 4. Copy .env.example to .env và điền thông tin
copy .env.example .env

# 5. Tạo database PostgreSQL (Railway/Neon/Local)
# Cập DATABASE_URL trong .env

# 6. Chạy migrations
uv run alembic upgrade head

# 7. Chạy bot
uv run python -m src.main
```
