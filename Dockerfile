FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

# Create .venv
RUN uv sync --frozen

COPY alembic.ini ./
COPY alembic/ ./alembic/

COPY entrypoint.sh ./
RUN chmod +x /app/entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]