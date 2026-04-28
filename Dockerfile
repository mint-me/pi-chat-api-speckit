FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM base AS test
COPY . .
RUN uv sync --frozen --dev

FROM base AS runtime
COPY . .
RUN useradd -r -u 1001 -g root -m -d /home/appuser appuser \
    && mkdir -p /home/appuser/.cache/uv \
    && chown -R appuser:root /app /home/appuser
ENV HOME=/home/appuser \
    UV_CACHE_DIR=/home/appuser/.cache/uv
USER appuser
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
