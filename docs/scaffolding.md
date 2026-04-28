# Scaffolding

High-level sequence:

1. Create the new repository root and initialize git on `main`.
2. Add base project files and package structure.
3. Scaffold the FastAPI package, settings, database helpers, and tests.
4. Add health, auth, model, chat, history, logging, and provider layers.
5. Add Alembic, Docker, Compose, smoke testing, CI, and documentation.

The code is intentionally narrow: one web app, one database, one LLM boundary,
and one deterministic mock for automated verification.

## FastAPI Skeleton Used

```python
from fastapi import FastAPI

app = FastAPI(title="Chat API")


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

### Alembic Database Migrations

`alembic/script.py.mako` is the Jinja2 template Alembic uses when generating
new migration files via `alembic revision`. It is created by `alembic init`
and is expected in all Alembic projects.

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

---

## How This Project Was Specified

This project used [spec-kit](https://github.com/github/spec-kit) v0.8.2 to manage
the specification-first workflow.

spec-kit generates the `.specify/` and `.agents/` infrastructure automatically
(the spec-kit framework templates and AI agent skill definitions). These
directories are gitignored because they are reproducible via `speckit init`.
The `specs/001-llm-chat-api/` directory contains the project-specific artifacts:
constitution, feature specification, research decisions, implementation plan,
and task list.

### Reinstalling spec-kit

To regenerate `.specify/` and `.agents/` from a clone (they are not tracked):

```bash
# Requires GitHub CLI (https://cli.github.com)
gh extension install github/spec-kit

# Initialize spec-kit in the project root
speckit init
```

This workflow used the spec-kit methodology: constitution → specification →
research → plan → tasks → implementation, with each step producing artifacts
in the `specs/` directory.
