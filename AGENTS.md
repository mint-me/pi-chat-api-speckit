<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
specs/001-llm-chat-api/plan.md
<!-- SPECKIT END -->

# Repository Guidelines

Guidelines for any AI agent, assistant, or contributor working on this codebase.
Read this file before writing code.

## Project Overview

Minimal LLM-powered chat API. Stack: FastAPI, PostgreSQL, SQLAlchemy 2.0 async,
Alembic, JWT, SSE, OpenRouter plus mock fallback.

This repository is the canonical spec-kit rebuild in `pi-chat-api-speckit/`.
Other chat projects in the workspace may be read for comparison only.

Remote publishing and collaborator invitations are out of scope.

## Directory Structure

```text
pi-chat-api-speckit/
├── app/           # FastAPI app, models, services, routers, security, logging
├── alembic/       # Database migrations
├── specs/         # spec-kit artifacts
├── tests/         # pytest suite
├── scripts/       # seed.py and smoke.py
├── docs/          # quickstart, architecture, local-dev, testing, ci, scaffolding
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── .env.example
```

## Commands

Run commands from the repository root.

- `make install` installs dependencies with `uv sync --dev`
- `make run` starts the API with reload
- `make migrate` applies Alembic migrations
- `make test` runs the test suite
- `make coverage` runs tests with branch coverage
- `make lint` runs Ruff checks
- `make format` formats the code with Ruff
- `make format-check` checks formatting only
- `make smoke` runs the live HTTP smoke script
- `make demo` starts Compose and seeds demo data
- `make docker-up` builds and starts the stack
- `make docker-down` stops and removes containers and volumes
- `make test-docker` runs pytest inside the Compose test container

Primary local entry point: `docker compose up --build`

## Coding Style

- Python 3.12
- Ruff is the source of truth. Use `E`, `F`, `I`, `B`, `UP`, `ASYNC`
- Line length: 100
- `snake_case` for functions, variables, and modules
- `PascalCase` for classes
- Full type hints on public functions
- Pydantic v2 only
- Async code everywhere in the request path
- Google-style docstrings on public functions and classes

## Architecture Rules

- Routers own HTTP concerns only
- Services own business logic
- All LLM access goes through `LLMClient`
- Do not hold a DB transaction during SSE streaming
- Persist the user message before streaming starts
- Persist the assistant message only after the stream completes
- Ownership checks must filter by `user_id`
- Cross-user access returns `404`, not `403`

## Testing Rules

- Use real SQLite or Postgres for DB tests, never a mocked DB
- Mock OpenRouter HTTP with `respx` in all automated tests
- Use `httpx.AsyncClient` with `ASGITransport` for in-process API tests
- Keep one end-to-end user journey test that covers register -> login -> chat -> history
- Keep live-stack checks in `scripts/smoke.py`, not pytest
- Tests should assert behavior, not implementation details

## Security Rules

- Never log prompts, responses, API keys, passwords, or JWT tokens
- Never commit `.env`
- Hash passwords with Argon2 via `pwdlib`
- JWT secret must come from env and be at least 32 characters
- Reject the default JWT secret in production
- Do not introduce refresh tokens, rate limiting, OTel, or Langfuse here

## Git Rules

- Use Conventional Commits
- One logical change per commit
- Do not amend published commits
- Do not add third-party invitation or submission automation
