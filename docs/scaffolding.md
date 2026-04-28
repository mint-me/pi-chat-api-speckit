# Scaffolding

This repository was rebuilt as a fresh project rather than patched in place.

High-level sequence:

1. Create the new repository root and initialize git on `main`.
2. Add `PLAN.md`, `AGENTS.md`, and `CLAUDE.md`.
3. Scaffold the FastAPI package, settings, database helpers, and tests.
4. Add health, auth, model, chat, history, logging, and provider layers.
5. Add Alembic, Docker, Compose, smoke testing, CI, and documentation.

The code is intentionally narrow: one web app, one database, one LLM boundary,
and one deterministic mock for automated verification.

## FastAPI Skeleton Used

```python
from fastapi import FastAPI

app = FastAPI(title="Pi School Chat API")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

Then the scaffold is expanded in this order:

1. Auth (`/auth/register`, `/auth/login`) with Argon2 + JWT
2. Chat streaming (`/chat`) with SSE events
3. History (`/chat/history`) with ownership checks
4. Alembic migration for users/conversations/messages
5. Docker Compose (`api`, `db`, optional `demo` seed)
6. Tests, smoke, CI, and docs

## Rebuild Commands (From Empty Workspace)

```bash
uv sync --dev
uv run alembic upgrade head
make lint
make test
docker compose up --build -d
make smoke
```

Expected verification order: lint -> tests -> compose health -> smoke.
