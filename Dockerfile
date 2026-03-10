FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy alembic and src
COPY pyproject.toml uv.lock ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
COPY scripts ./scripts

# Install uv
RUN pip install uv

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Make start script executable
RUN chmod +x scripts/start.sh

# Copy .env.example as default (users should mount their own .env)
COPY .env.example .env.example

# Expose port for bot (if needed)
EXPOSE 8080

# Run the bot with migration
CMD ["./scripts/start.sh"]
