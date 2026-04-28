# Plan — Pi School ML Systems Take-Home: Clean Rebuild

## Context

Step-2 take-home for **Software Engineer (ML Systems)** at Pi School. Followed by 45–60 min live walkthrough. The hire ships LLM systems on **EVE** (Earth Observation assistant for ESA, FastAPI + MongoDB + Qdrant + LangGraph) and **Meetween** (multimodal speech, EU project).

Assignment principle (verbatim): **"simple and correct beats complex and impressive"**. Time budget ~4h, 96h deadline.

A working draft exists at `pi-school-chat-api/` (won't be modified). Two parallel audits confirmed it's functionally complete but has issues that hurt the **submission narrative**: mixed-quality git history (fix-up commits next to feat commits), `.env` tracked at some point, bare `assert` in the SSE generator, root-user container, three-mode provider enum that adds explanation overhead. The existing test suite is technically E2E-shaped via `httpx.AsyncClient` but lacks an automated end-to-end **user journey** test, lacks an automated smoke runner against a live container, and lacks a one-command "demo" path that gives reviewers a pre-seeded experience.

User-confirmed scoping (recorded for the implementer):
- **Strategy**: rebuild in a **new directory** with **fresh git init**, copying working code from the existing PoC where it's good. The old PoC stays untouched as reference.
- **Observability**: stdlib structured JSON logging only — no OpenTelemetry, no Langfuse. EVE itself does not use OTel.
- **Docs language**: English (matches EVE/MeetWeen).
- **LLM provider**: presence of `OPENROUTER_API_KEY` decides — no enum.
- **Tests**: mocked HTTP only in CI. No live OpenRouter call from automation.
- **Real LLM key**: candidate sets `OPENROUTER_API_KEY` locally in `.env` (untracked) when they want to test real inference.

What **changed** vs the previous plan after user feedback:
1. Clean rebuild in a new repo, not in-place polish.
2. Database choice **defended explicitly** in dedicated section + interview script.
3. **FastAPI E2E test** — single end-to-end "user journey" test using `httpx.AsyncClient` + `ASGITransport` per the official FastAPI testing guide, parsing the actual SSE stream.
4. **Automated seed** via Compose `demo` profile — `docker compose --profile demo up` gives pre-populated DB.
5. **Automated smoke** — `scripts/smoke.py` (httpx, assertions, no extra deps) + `make smoke`. Replaces "copy/paste curl from README".

## New Project Location

Build directory: `/home/psych0/Projects/PiCampus/SWE/pi-chat-api-speckit/`

Fresh `git init`. The candidate can rename the directory before submission if desired (e.g., to `pi-school-chat-api`). The old `pi-school-chat-api/` stays in place untouched as a reference and as fallback.

The implementation pulls verbatim from the old PoC where the code is correct (~70-80% reuse expected): SQLAlchemy models, schemas, services, alembic env, security helpers, conftest, ruff config. It rewrites:
- `app/config.py` (drop provider enum, tighten JWT defaults)
- `app/routers/chat.py` (replace bare `assert`)
- `app/services/llm.py` (key-driven factory)
- `app/main.py` (add request-id middleware + JSON logging)
- `Dockerfile` (non-root runtime stage)
- `docker-compose.yml` (api healthcheck + demo profile)
- `.env.example` (drop `LLM_PROVIDER`, default to free OpenRouter model)
- `README.md` + new `docs/` index
- Tests: add `tests/test_user_journey.py` for full E2E flow

## Database — PostgreSQL Defense (the question that matters most)

The single hardest interview question will be: *"Why PostgreSQL when EVE uses MongoDB?"* The plan articulates this explicitly so the candidate doesn't improvise.

**The thesis**: PostgreSQL is the right call for **this** assignment, even though Mongo is right for EVE's data shape. The skill on display is choosing storage based on the **shape of the data and the operations on it**, not based on what the team uses for a different product.

**Five points the candidate states verbatim if asked**:

1. **The job description names PostgreSQL.** Pi School's JD lists "relational databases including PostgreSQL" among required skills. Choosing it puts the strongest possible signal that the candidate can model relationally — the exact skill the JD asks for.

2. **The data is strictly relational.** Three entities, two ownership relationships:
   ```
   users (1) ──< conversations (1) ──< messages
   ```
   A user owns conversations. A conversation owns messages. Ownership is a hard constraint, not a soft one. Foreign keys with `ON DELETE CASCADE` express that constraint **at the schema level**, so it cannot be violated by application bugs.

3. **The constraint set is non-trivial and pays off.**
   - `UNIQUE (email)` — prevents duplicate accounts at the DB layer, removes a class of race conditions.
   - `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE` — ownership chain.
   - `CHECK (role IN ('user', 'assistant'))` — domain validation in the DB.
   - Composite index `(user_id, updated_at DESC)` — direct match for "list a user's conversations newest-first".
   - Composite index `(conversation_id, created_at)` — direct match for "load this conversation's messages in order".
   These are real engineering choices, each tied to a real query.

4. **Alembic comes for free.** Schema migrations are one of the assignment's stretch items. PostgreSQL + Alembic is the natural pair. With Mongo, the candidate would have to skip this stretch or simulate it.

5. **The honest acknowledgment of EVE.** *"EVE uses MongoDB because it stores semi-structured Earth-observation context, retrieved chunks, embeddings, evaluation metadata — variable-shape documents. That's the right choice for that data. The data this assignment asks me to model is the opposite: stable shape, strict ownership, fixed three-table topology. Different problem, different storage. The skill being demonstrated isn't 'pick what the team uses', it's 'pick based on the data'."*

**Trade-off the candidate volunteers (shows maturity)**: *"If the assistant later needs to store variable-shape provider metadata per message — tool calls, retrieved citations, evaluation scores — I keep a `JSONB` column for that. PostgreSQL gives me both: relational shape for the things that need constraints, JSON for the things that don't."* The schema includes `messages.provider_metadata JSONB NULL` for exactly this.

**What to avoid saying**: "MongoDB is bad" / "PostgreSQL is more enterprise" / "I prefer SQL" — all weak. The strong answer is data-shape-first.

## Architecture (boundaries, kept simple)

```
HTTP request
  └── FastAPI router (app/routers/{auth,chat,health}.py)
      ├── Pydantic schema validation (app/schemas/)
      ├── Depends(CurrentUser) → JWT decode (app/security.py)
      └── Service layer (app/services/{auth_service,chat_service,llm}.py)
          ├── SQLAlchemy 2.0 async session (app/database.py)
          └── LLMClient (OpenRouter | Mock)  ← key-driven factory
```

Logging is a thin contextvar-bound JSON logger (`app/logging.py`, ~50 lines, stdlib only). Each request gets a `request_id` UUID, set by an ASGI middleware, surfaced in the `X-Request-ID` response header, and bound to every log record from that request via `contextvars.ContextVar`.

Single boundary worth defending: the **`LLMClient` interface**. Two methods (`stream(messages) -> AsyncIterator[str]`, plus a name property for logging). OpenRouter and Mock both implement it. Tomorrow a `RunPodClient`, `vLLMClient`, `BentoMLClient` slot in behind the same interface without changing the chat service. This is the single architectural decision that maps directly to the JD's "model-serving frameworks (FastAPI, BentoML, vLLM, Triton)" line.

## Repository Layout

```
pi-chat-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # create_app() factory, lifespan, middleware registration
│   ├── config.py            # pydantic-settings, env-driven, validators
│   ├── database.py          # async engine, sessionmaker, get_session()
│   ├── deps.py              # SessionDep, CurrentUserDep
│   ├── errors.py            # AppError + handler
│   ├── logging.py           # JSON formatter, request_id contextvar, ASGI middleware  [NEW]
│   ├── security.py          # password hashing (Argon2/pwdlib), JWT encode/decode
│   ├── models.py            # SQLAlchemy 2.0 Mapped[] models: User, Conversation, Message
│   ├── types.py             # GUID TypeDecorator (cross-DB UUID)
│   ├── schemas/
│   │   ├── auth.py          # RegisterRequest, LoginRequest, TokenResponse, UserResponse
│   │   └── chat.py          # ChatRequest, MessageResponse, ConversationResponse, HistoryResponse
│   ├── routers/
│   │   ├── auth.py          # POST /auth/register, POST /auth/login
│   │   ├── chat.py          # POST /chat (SSE), GET /chat/history
│   │   └── health.py        # GET /health
│   └── services/
│       ├── auth_service.py  # register_user, authenticate_user
│       ├── chat_service.py  # prepare_chat, stream_assistant_response (no tx during stream)
│       └── llm.py           # LLMClient ABC, OpenRouterClient, MockClient, get_llm_client()
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_schema.py
├── tests/
│   ├── conftest.py          # async client fixture, fresh schema per test, mocked HTTP
│   ├── test_health.py
│   ├── test_auth.py         # register dup, register weak password, login wrong password, login JSON-not-form
│   ├── test_chat.py         # SSE event stream contract, persistence, error event, ownership
│   ├── test_history.py      # cross-user 404, ordering, empty list
│   ├── test_llm_provider.py # no-key → mock; key → OpenRouter (mocked HTTP); streaming parser
│   └── test_user_journey.py # full E2E: register → login → chat (parse SSE) → history       [NEW]
├── scripts/
│   ├── seed.py              # creates demo user + sample conversation
│   └── smoke.py             # E2E HTTP smoke against live server, asserts, exit code   [NEW]
├── docs/
│   ├── quickstart.md        # 0-to-running in 5 minutes
│   ├── architecture.md      # diagram + boundaries + decisions + next steps
│   ├── local-dev.md         # uv workflow, alembic, ruff, pytest
│   ├── testing.md           # how tests are organized, how to run E2E and smoke    [NEW]
│   └── ci.md                # CI rationale (kept from existing PoC)
├── .github/workflows/ci.yml
├── alembic.ini
├── Dockerfile               # multi-stage: base → test, base → runtime (non-root)
├── docker-compose.yml       # services: db, api (with healthcheck), test (profile), seed (profile)
├── .dockerignore
├── .env.example
├── .gitignore
├── AGENTS.md                # Repository Guidelines (moved from workspace root)
├── Makefile                 # install, lint, format, test, coverage, smoke, demo, run, docker-up, docker-down
├── pyproject.toml
├── uv.lock
└── README.md
```

## E2E Testing Strategy (FastAPI official + practical)

Per the FastAPI testing guide (https://fastapi.tiangolo.com/tutorial/testing/) and the async-app extension (`httpx.AsyncClient` + `ASGITransport`), tests live at three levels:

1. **Per-router behavior tests** — one file per concern (`test_auth.py`, `test_chat.py`, `test_history.py`, `test_llm_provider.py`). Each uses the in-process app with a SQLite-backed fixture (existing PoC pattern via `aiosqlite`) for speed and isolation. OpenRouter HTTP is mocked with `respx`. These tests assert specific contracts and edge cases.

2. **End-to-end user journey** — single new file `tests/test_user_journey.py`. One test that runs the full happy path:
   ```python
   async def test_full_user_journey(async_client, mocked_openrouter):
       # 1. Register
       r = await async_client.post("/auth/register", json={"email": "alice@example.com", "password": "password123"})
       assert r.status_code == 201

       # 2. Login
       r = await async_client.post("/auth/login", json={"email": "alice@example.com", "password": "password123"})
       token = r.json()["access_token"]
       headers = {"Authorization": f"Bearer {token}"}

       # 3. Chat (SSE) — parse the stream
       events = []
       async with async_client.stream("POST", "/chat", json={"message": "Hello", "conversation_id": None}, headers=headers) as resp:
           assert resp.status_code == 200
           assert resp.headers["content-type"].startswith("text/event-stream")
           async for line in resp.aiter_lines():
               if line.startswith("event:") or line.startswith("data:"):
                   events.append(line)
       # Assert we saw at least one token event and one done event
       assert any(e == "event: token" for e in events)
       assert any(e == "event: done" for e in events)

       # 4. History
       r = await async_client.get("/chat/history", headers=headers)
       assert r.status_code == 200
       conversations = r.json()["conversations"]
       assert len(conversations) == 1
       assert len(conversations[0]["messages"]) == 2  # user + assistant
       assert conversations[0]["messages"][0]["role"] == "user"
       assert conversations[0]["messages"][1]["role"] == "assistant"
   ```
   This test alone proves the assignment delivers. If this passes, the four required endpoints work together.

3. **Container smoke** (out-of-process, optional in CI) — `docker compose --profile test run --rm test` runs the full pytest suite inside the same image reviewers will use. Already implemented in the PoC; carry over verbatim.

Plus the Compose-level reviewer simulation in CI: `docker compose up -d --build`, hit `/health`, run `scripts/smoke.py`. This is the strongest "it actually works on the reviewer's machine" signal, and replaces the current curl-in-a-shell-script CI step.

## Automated Seed Path

Compose gets a `demo` profile that runs the existing `scripts/seed.py` after `db` and `api` are healthy:

```yaml
services:
  # ... db, api as before ...
  seed:
    build: { context: ., target: runtime }
    profiles: ["demo"]
    env_file: [.env]
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/pi_chat
    depends_on:
      api: { condition: service_healthy }
    command: ["uv", "run", "--no-sync", "python", "scripts/seed.py"]
    restart: "no"
```

Reviewer flow:
- `docker compose up --build` → empty DB, register your own user (default).
- `docker compose --profile demo up --build` → empty DB + automatic seed of `demo@example.com` / `password123` with one sample conversation. **One command to play.**

`scripts/seed.py` is idempotent (skip-if-exists by email).

`make demo` shorthand: `docker compose --profile demo up --build`.

## Automated Smoke Test (replaces curl spam)

`scripts/smoke.py` — pure Python, uses `httpx` (already a dependency), no new deps:

```python
"""End-to-end smoke test against a running pi-chat-api.

Usage: python scripts/smoke.py [BASE_URL]
Exit code 0 on success, non-zero on failure with diagnostic output.
"""
import asyncio, os, sys, uuid, httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

async def main() -> int:
    email = f"smoke+{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as c:
        r = await c.get("/health"); assert r.status_code == 200, r.text
        r = await c.post("/auth/register", json={"email": email, "password": password}); assert r.status_code == 201, r.text
        r = await c.post("/auth/login", json={"email": email, "password": password}); assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        H = {"Authorization": f"Bearer {token}"}
        async with c.stream("POST", "/chat", json={"message": "Say hi briefly.", "conversation_id": None}, headers=H) as resp:
            assert resp.status_code == 200, await resp.aread()
            assert resp.headers["content-type"].startswith("text/event-stream")
            saw_token = saw_done = False
            async for line in resp.aiter_lines():
                if line == "event: token": saw_token = True
                if line == "event: done": saw_done = True
            assert saw_token and saw_done, "missing SSE events"
        r = await c.get("/chat/history", headers=H); assert r.status_code == 200, r.text
        assert r.json()["conversations"], "history empty"
        print(f"OK — health, register, login, chat (SSE), history all pass for {email}")
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

`make smoke` runs `python scripts/smoke.py`. CI runs it after `docker compose up -d --build`. README points reviewers at it as the **one-command verification**.

This is much stronger than the existing curl block: copy-paste-resistant, asserts on event types, prints a diagnostic on failure.

## Other Polish (carried from previous plan)

These are settled; listing them once:
- Drop `LLM_PROVIDER` enum from `Settings` and `.env.example`. Provider is key-driven.
- `JWT_SECRET_KEY`: `min_length=32`. Validator rejects the literal default when `ENVIRONMENT=production` (new field, defaults to `development`).
- `app/routers/chat.py`: replace `assert database.SessionLocal is not None` with explicit guard that emits an SSE `error` event and returns; wrap the loop in try/except that emits `error` on unexpected exceptions.
- `Dockerfile`: add `RUN useradd -r -u 1001 -g root appuser && chown -R appuser:root /app` + `USER appuser` in `runtime` stage only.
- `docker-compose.yml`: `api` healthcheck via Python urllib hitting `/health`.
- `.env.example`: default `OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct:free` (free tier, lets reviewers test real inference without billing).
- Drop the explicit `assert`-style internal checks; rely on FastAPI/Pydantic to enforce contract at the boundary.
- Move `AGENTS.md` from workspace root into `pi-chat-api/AGENTS.md` so it travels with the repo.

## Tasks (mapped to commits)

Each task corresponds to one commit. Each commit is independently complete and tested at HEAD: a reviewer who checks out any commit can run `pytest` and see green for the scope at that point. The candidate must be able to answer "what does this commit prove?" for any single one.

**T0 — Pre-development (this is the only task that runs while still under planning)**:
- Create `/home/psych0/Projects/PiCampus/SWE/pi-chat-api/` directory.
- Inside it: write `PLAN.md` (full content of this plan), `AGENTS.md` (LLM/agent guidelines per the section above), and a one-line `CLAUDE.md` (`# See AGENTS.md`).
- **STOP**. Wait for user to read the plan in the new directory and explicitly authorize T1.

**T1 — `chore: scaffold FastAPI project with uv and ruff`**
- `cd pi-chat-api && git init -b main`
- `uv init --package --name pi-chat-api .` (or `uv init` then edit `pyproject.toml`)
- `uv add fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg "psycopg[binary]" alembic pydantic-settings pyjwt "pwdlib[argon2]" httpx email-validator`
- `uv add --dev pytest pytest-asyncio pytest-cov respx ruff aiosqlite coverage`
- Create `app/__init__.py`, `app/main.py` (`create_app()` factory, lifespan placeholder), `app/config.py` (Settings with env), `tests/conftest.py` (async client fixture), `.gitignore`, `.env.example` (full vars list, all empty/dummy), `Makefile` (install, lint, format, test, coverage, run targets), `pyproject.toml` ruff/pytest config blocks.
- Verify: `uv run ruff check . && uv run ruff format --check .` passes.
- Commit.

**T2 — `feat: add health endpoint`**
- `app/routers/health.py` with `GET /health` returning `{"status":"ok"}`.
- Register router in `create_app()`.
- `tests/test_health.py` asserts 200 and body.
- Verify: `uv run pytest -q`.
- Commit.

**T3 — `feat: add PostgreSQL models and Alembic migration`**
- `app/types.py` (GUID TypeDecorator for cross-DB UUID, with docstring explaining cross-DB rationale).
- `app/models.py` (User, Conversation, Message — SQLAlchemy 2.0 `Mapped[]` style, FKs with CASCADE, indexes, CHECK on `role`).
- `app/database.py` (async engine, sessionmaker, `get_session()` dep).
- `alembic init alembic` then customize `alembic/env.py` to use async + read `DATABASE_URL` from `Settings`.
- Generate initial migration: `alembic revision --autogenerate -m "initial schema"`. Hand-edit if needed for cleanliness.
- `tests/test_models.py` smoke test for table creation against in-memory SQLite.
- Verify: `uv run alembic upgrade head` against a Compose-managed Postgres works; tests pass.
- Commit.

**T4 — `feat: add user registration with Argon2 hashing`**
- `app/security.py` — `hash_password`, `verify_password` via `pwdlib` Argon2.
- `app/schemas/auth.py` — `RegisterRequest` (EmailStr + min length), `UserResponse`.
- `app/services/auth_service.py` — `register_user(session, email, password)` with normalize-email and duplicate handling.
- `app/errors.py` — `AppError` + handler in `create_app()`.
- `app/routers/auth.py` — `POST /auth/register`, returns 201.
- `tests/test_auth.py::test_register_*` — happy path, duplicate (409), case-insensitive duplicate (409), weak password (422), invalid email (422), no plaintext password persisted.
- Commit.

**T5 — `feat: implement JWT authentication and protected dependency`**
- `app/security.py` — `create_access_token`, `decode_access_token`.
- `app/schemas/auth.py` — `LoginRequest`, `TokenResponse`.
- `app/services/auth_service.py` — `authenticate_user`.
- `app/deps.py` — `CurrentUserDep`, `SessionDep` (HTTP Bearer extraction → user load).
- `app/routers/auth.py` — `POST /auth/login`.
- `tests/test_auth.py::test_login_*` — happy path, wrong password (401), wrong email (401), JSON not form-data, protected dummy endpoint rejects missing/invalid token.
- Commit.

**T6 — `feat: add LLM provider boundary with mock client`**
- `app/services/llm.py` — `LLMClient` ABC (`stream(messages) -> AsyncIterator[str]`, `name: str`), `MockClient` with realistic 200–500ms chunk delays for ~5 tokens, `get_llm_client(settings)` factory (mock-only at this point, OpenRouter added in T9).
- `tests/test_llm_provider.py::test_mock_client_streams` — asserts iterable yields token chunks within delay budget.
- Commit.

**T7 — `feat: add streaming chat endpoint with SSE`**
- `app/schemas/chat.py` — `ChatRequest`.
- `app/services/chat_service.py` — `prepare_chat` (create or validate conversation, persist user message, commit), `stream_assistant_response` (consume `LLMClient.stream`, yield events, persist assistant message in a fresh session after stream completes, no DB tx held during stream).
- `app/routers/chat.py` — `POST /chat`, builds `StreamingResponse(..., media_type="text/event-stream")`, explicit guard for `database.SessionLocal is None` (no `assert`), try/except for unexpected errors → SSE error event.
- `tests/test_chat.py` — unauthenticated 401, authenticated returns SSE, stream contains `event: token` and `event: done`, user and assistant messages persisted, provider failure emits `event: error` and does not persist a complete assistant message.
- Commit.

**T8 — `feat: add conversation history with ownership scoping`**
- `app/schemas/chat.py` — `MessageResponse`, `ConversationResponse`, `HistoryResponse`.
- `app/services/chat_service.py` — `get_history(session, user, conversation_id=None)`.
- `app/routers/chat.py` — `GET /chat/history` with optional `conversation_id` query.
- `tests/test_history.py` — user sees own history, cross-user `conversation_id` returns 404 (not 403), messages ordered by `created_at`, empty history returns `[]`.
- Commit.

**T9 — `test: add end-to-end user journey`**
- `tests/test_user_journey.py::test_full_user_journey` — register → login → POST /chat (parse SSE stream) → GET /chat/history. Asserts `event: token` and `event: done` are present, history contains both user and assistant messages in order.
- Verify: this single test passes against the in-process app.
- Commit.

**T10 — `feat: add OpenRouter provider with mocked HTTP tests`**
- `app/services/llm.py` — `OpenRouterClient(api_key, model, base_url)` implementing `stream`. Calls `POST {base_url}/chat/completions` with `stream=true`, parses SSE `data:` lines, ignores comments, stops on `data: [DONE]`, extracts `choices[0].delta.content`. 30s timeout. Wraps network errors in a small `ProviderError`.
- Update `get_llm_client(settings)` to return `OpenRouterClient` when `settings.openrouter_api_key` is set, else `MockClient`. **No enum.**
- `tests/test_llm_provider.py` — no key → mock; key → OpenRouter (with `respx`-mocked HTTP returning a fake SSE stream); streaming parser handles `[DONE]`, blank lines, multi-chunk tokens.
- Commit.

**T11 — `feat: add structured JSON logging with request id`**
- `app/logging.py` — JSON formatter (timestamp, level, logger, message, request_id, plus extra fields), `request_id_var: ContextVar[str]`, ASGI `RequestIdMiddleware` that sets the contextvar and adds `X-Request-ID` to the response.
- `app/main.py` — register middleware, configure logger in `lifespan`.
- Add `logger.info("event", extra={"event": "chat.start", "user_id": ..., "conversation_id": ...})`-style calls in `chat_service.py` and `llm.py` (`chat.llm_done` with `provider`, `model`, `chunk_count`, `latency_ms`; `chat.llm_error` with `provider`, `error_class`, `latency_ms`). **Never log prompt/response content or API keys.**
- `tests/test_logging.py` (light) — request to `/health` produces a JSON log line with `request_id` matching the response header.
- Commit.

**T12 — `chore: add Dockerfile, compose with healthcheck, and demo seed profile`**
- `Dockerfile` — multi-stage `base → test`, `base → runtime`. Runtime stage adds `useradd -r -u 1001 -g root appuser && chown -R appuser:root /app` and `USER appuser`. Test stage stays root for coverage writes.
- `.dockerignore` — `.env`, `.venv`, `.git`, `__pycache__`, `.pytest_cache`, `.ruff_cache`, `.coverage`, `tests/` (only excluded for runtime via stage logic, included for test stage).
- `docker-compose.yml` — `db` (Postgres 16 + healthcheck), `api` (depends_on db healthy, env_file, port 8000, **its own healthcheck via Python urllib hitting `/health`**), `test` profile, `seed` profile (runs `scripts/seed.py` once, depends on api healthy).
- `scripts/seed.py` — idempotent: skip-if-`demo@example.com`-exists, otherwise create + sample conversation.
- `scripts/smoke.py` — full HTTP smoke via httpx (registers fresh user with random suffix, login, chat with SSE parsing, history). Exit 0/non-zero with diagnostic.
- `Makefile` adds `docker-up`, `docker-down`, `demo` (`docker compose --profile demo up --build`), `smoke` (`python scripts/smoke.py`), `test-docker`.
- Verify: from clean state, `docker compose down -v && cp .env.example .env && docker compose up -d --build && python scripts/smoke.py` all green; container runs as uid 1001; healthcheck reports healthy.
- Commit.

**T13 — `ci: run lint, tests, and live compose smoke`**
- `.github/workflows/ci.yml` — two jobs:
  - `quality`: setup-python 3.12, install uv, `uv sync --frozen --all-extras --dev`, Postgres service container, `uv run alembic upgrade head`, `uv run ruff check . && uv run ruff format --check .`, `uv run pytest --cov=app --cov-fail-under=80`.
  - `compose-smoke`: setup Docker buildx, `cp .env.example .env`, `docker compose up -d --build`, wait for `/health`, `python scripts/smoke.py http://localhost:8000`, dump `docker compose logs api` on failure.
- No GitHub Secrets required. No live OpenRouter call.
- Commit.

**T14 — `docs: add README, AGENTS, and the docs/ folder`**
- `README.md` — Quick Start (5 lines), Documentation index (one line per `docs/` file), Configuration (env vars table), API overview, four design decisions (≤4 lines each), Testing (3 commands), Security notes, "What I'd do next", AI tools disclosure.
- `docs/quickstart.md` — running the **already-built** project, two paths (clean / `--profile demo`), real-LLM optional via key.
- `docs/scaffolding.md` — **how the project was built from zero**, command-by-command, mirroring T1–T14 above. Includes the rationale for each major dependency choice.
- `docs/architecture.md` — diagram + boundaries + four decisions + next steps.
- `docs/local-dev.md` — uv + alembic + ruff + pytest workflow.
- `docs/testing.md` — three test layers, when to add a test, mocking strategy.
- `docs/ci.md` — pipeline rationale.
- `AGENTS.md` already exists from T0; verify content still accurate (no field references stale code).
- Commit.

**Total: 14 commits (T1–T14), plus T0 as a pre-development setup commit inside the new repo (`PLAN.md` + `AGENTS.md` + `CLAUDE.md`).**

If time pressure forces shortcuts, drop in this priority order: T14 (docs) → T13 (CI) → T11 (logging) → T9 (e2e test). Never sacrifice T1–T8 or T10 or T12 — they are the assignment core.

## Definition of Done

- [ ] All 14 task commits present in `pi-chat-api/` git log, each with a short imperative subject and a brief body explaining the why.
- [ ] `uv run pytest --cov=app --cov-fail-under=80` green.
- [ ] `tests/test_user_journey.py::test_full_user_journey` passes.
- [ ] `docker compose down -v && cp .env.example .env && docker compose up -d --build` reaches healthy state within 30s.
- [ ] `python scripts/smoke.py` passes against the running stack.
- [ ] `docker compose --profile demo up --build` produces a queryable `demo@example.com` account.
- [ ] `docker compose --profile test run --rm test` runs the full suite green inside the runtime image.
- [ ] `docker compose exec api id` returns uid 1001 (not root).
- [ ] Manual real-LLM check (optional, with candidate's own key): `OPENROUTER_API_KEY=sk-or-v1-... docker compose up -d --build && python scripts/smoke.py` returns tokens from the real model; logs show `provider=openrouter`, no leaked content.
- [ ] `git ls-files | grep -E '(^|/)\.env$'` returns nothing.
- [ ] `git log --all --diff-filter=A --name-only | grep -E '(^|/)\.env$'` returns nothing (no historical leak).
- [ ] README, AGENTS.md, all five `docs/*.md` files present and cross-linked.
- [ ] Candidate has rehearsed the live-walkthrough script and can defend each commit.

## Documentation Files (all cited in README)

- `docs/quickstart.md` — running the **already-built** project: clone, `cp .env.example .env`, `docker compose up --build`, `python scripts/smoke.py`. Two paths: clean start vs `docker compose --profile demo up`. Real LLM optional via `OPENROUTER_API_KEY`.
- `docs/scaffolding.md` — **how the project was built from zero**, command-by-command. For someone who wants to understand the construction (e.g., to evaluate the candidate's process or rebuild the project from scratch). Covers: `uv init`, `uv add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic pydantic-settings pyjwt pwdlib[argon2] httpx email-validator`, `uv add --dev pytest pytest-asyncio pytest-cov respx ruff aiosqlite coverage`, directory layout creation, `alembic init alembic`, `ruff` config block, initial migration commands, Dockerfile/compose authoring rationale, the 14-commit sequence. **This file is the candidate's audit trail of the work.**
- `docs/architecture.md` — request-flow diagram (Mermaid), layer boundaries, four design decisions (PostgreSQL, SSE, OpenRouter+mock, JWT) with 3-line rationale each. "What's next" section: rate limiting, OTel/Langfuse, refresh tokens, Qdrant for RAG, GPU providers behind the LLMClient interface.
- `docs/local-dev.md` — `uv sync --dev`, `uv run alembic upgrade head`, `uv run pytest -q`, ruff, running uvicorn with `--reload` against compose-managed Postgres.
- `docs/testing.md` — three layers explained: per-router unit-ish tests, `test_user_journey.py` E2E in-process, `scripts/smoke.py` against live container. Mocking strategy (`respx`). When to add a test.
- `docs/ci.md` — CI rationale, updated to reflect the new smoke step.

## LLM/Agent Guidelines File

`pi-chat-api/AGENTS.md` (project root, tool-agnostic, recognized by Codex CLI / Cursor / many AI tools) is the **single source of truth for any AI agent or human contributor working on this codebase**. Content:

- **Project structure**: `app/`, `tests/`, `docs/`, `scripts/`, `alembic/` — what each folder owns.
- **Commands**: `make install / lint / format / test / coverage / smoke / demo / run / docker-up / docker-down`. Reviewer entry point: `docker compose up --build`.
- **Coding style**: Python 3.12, ruff as source of truth (`E,F,I,B,UP,ASYNC` rules), line length 100, snake_case for functions/vars/modules, PascalCase for classes, **no camelCase anywhere**, full type hints required, async everywhere, Pydantic v2 only (no plain dataclasses), Google-style docstrings on public functions.
- **Architecture rules**: routers own HTTP only, services own business logic, LLM calls go through `LLMClient` interface, no DB transaction held during streaming, persist user message before stream starts, persist assistant message after stream completes, never duplicate `user_id` on `messages` (derive ownership through `conversation.user_id`).
- **Testing rules**: tests assert behavior not implementation; OpenRouter HTTP is always mocked (`respx`); use `httpx.AsyncClient` + `ASGITransport` per FastAPI testing guide; one `test_user_journey.py` covers the full happy path; CI must be deterministic and require no secrets.
- **Security rules**: never log prompts, responses, or API keys; never commit `.env`; passwords use Argon2 (`pwdlib`), never SHA-256/MD5; JWT secret comes from env, ≥32 chars; protected routes always validate the bearer token; ownership checks on every history/conversation read; cross-user resource access returns `404` not `403` (don't reveal existence).
- **Git rules**: Conventional Commits (`feat:`, `fix:`, `chore:`, `ci:`, `test:`, `docs:`, `refactor:`); imperative, lowercase subject; one logical change per commit; never amend a published commit.
- **What NOT to add** (anti-overengineering list): no Qdrant/RAG; no Redis; no Kubernetes manifests; no MkDocs site; no refresh tokens; no rate limiting in core; no OpenTelemetry/Langfuse (next-step in `docs/architecture.md`); no vLLM/Triton/BentoML clients (slot behind `LLMClient` later); no live OpenRouter calls in CI.

For Claude Code specifically, a one-line `CLAUDE.md` may exist with `# See AGENTS.md` so both conventions are honored without duplication.

## Compose Profile Naming Decision

Two profiles in `docker-compose.yml`:
- **`test`** — runs the pytest suite inside the runtime image (carried over from the existing PoC, EVE-style). Command: `docker compose --profile test run --rm test`.
- **`demo`** — populates the database with `scripts/seed.py` (`demo@example.com` / `password123` + one sample conversation) so reviewers can `make demo` and immediately call `/chat/history`. Command: `docker compose --profile demo up --build`.

Naming rationale: in compose conventions `test` ≡ run-the-test-suite, while `demo`/`seed` ≡ load-sample-data. Reusing `test` for both would conflate two unrelated concerns. If you prefer `seed` over `demo`, the change is one-line.

README structure:
- Project overview (3 lines)
- Quick Start (5 lines, copy-pasteable)
- Documentation index (one line per `docs/` file)
- Configuration (env vars table)
- API overview (4 endpoints, link to `/docs`)
- Design decisions (4 paragraphs, each ≤4 lines: PostgreSQL, SSE, OpenRouter+mock, JWT)
- Testing (3 commands: `make test`, `make smoke`, `docker compose --profile test run --rm test`)
- Security notes
- What I'd do next (rate limiting, OTel, refresh tokens, RAG/Qdrant, GPU providers)
- AI tools disclosure

## Verification (run these to declare done)

From inside `pi-chat-api/`:

1. **Unit and integration**:
   ```bash
   uv sync --dev
   uv run ruff check . && uv run ruff format --check .
   uv run alembic upgrade head
   uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
   ```
   Expect: green, includes `test_user_journey.py`, coverage ≥80%.

2. **Container build + run**:
   ```bash
   docker compose down -v
   cp .env.example .env
   docker compose up -d --build
   docker compose ps                          # api healthy after ~15s
   docker compose exec api id                 # uid=1001, not root
   ```

3. **Live smoke (no key, mock provider)**:
   ```bash
   python scripts/smoke.py http://localhost:8000
   # → "OK — health, register, login, chat (SSE), history all pass for smoke+...@example.com"
   ```

4. **Demo profile**:
   ```bash
   docker compose down -v
   docker compose --profile demo up -d --build
   curl -s -X POST http://localhost:8000/auth/login -H 'Content-Type: application/json' \
     -d '{"email":"demo@example.com","password":"password123"}' | grep access_token
   ```

5. **Real OpenRouter (manual, optional)**:
   - Add `OPENROUTER_API_KEY=sk-or-v1-...` to local `.env`.
   - `docker compose down && docker compose up -d --build && python scripts/smoke.py`.
   - Inspect logs: `docker compose logs api | grep '"event":"chat.llm_done"'` — confirm `provider=openrouter`, `model=meta-llama/llama-3.2-3b-instruct:free`, non-zero `latency_ms`, no leaked content.

6. **Container test profile**:
   ```bash
   docker compose --profile test run --rm test
   ```
   Expect: lint, format, migrations, full pytest pass inside the runtime image.

7. **Secrets sanity**:
   ```bash
   git ls-files | grep -E '(^|/)\.env$' && echo "FAIL" || echo "OK: no .env tracked"
   git log --all --diff-filter=A --name-only | grep -E '(^|/)\.env$' && echo "FAIL: ever tracked" || echo "OK: never tracked"
   ```

8. **Docs sanity**: a colleague who has never seen this project follows `docs/quickstart.md` on a clean clone and reaches a working `/chat` call without reading any other file. If they need to ask one question, the doc is wrong.

## Out of Scope (explicit, by user decision)

- **Submission**: no `git push`, no `gh repo create`, no collaborator invitations. The candidate ships manually.
- **OpenTelemetry / Langfuse / Phoenix**: not added. Future-work paragraph in `docs/architecture.md`.
- **Rate limiting, refresh tokens, password policy hardening**: README "What I'd do next".
- **RAG, Qdrant, vLLM, Triton, BentoML, NeMo, NVIDIA stack, GPU**: explicitly mentioned as evolution paths in `docs/architecture.md`, not implemented.
- **Live OpenRouter test in CI**: deliberately not added; tests stay deterministic.
- **Frontend**: assignment explicitly excludes UI.

## Approval Workflow (Two-Step)

The user wants a hard checkpoint between **plan staged** and **code written**. So this plan splits approval into two steps:

**Step A — Stage the plan inside the new directory** (T0 only):
On the first `ExitPlanMode` approval I will execute exactly these actions, nothing else:
1. `mkdir -p /home/psych0/Projects/PiCampus/SWE/pi-chat-api`
2. Write `pi-chat-api/PLAN.md` with the full content of this plan.
3. Write `pi-chat-api/AGENTS.md` with the LLM/agent guidelines content (per the section above).
4. Write `pi-chat-api/CLAUDE.md` with one line: `# See AGENTS.md`.
5. **STOP**. No `git init`, no `uv init`, no app code. The user reads `pi-chat-api/PLAN.md` and `AGENTS.md` in the new directory.

**Step B — Build** (T1–T14):
Only after the user explicitly says "go" / "vai" / "ok parti" do I begin T1. From then on the implementation runs as 14 clean commits as described in the Tasks section. Each task ends with running its scoped tests and committing.

The old `pi-school-chat-api/` is left untouched throughout. The candidate can compare, copy, or fall back at any time.
