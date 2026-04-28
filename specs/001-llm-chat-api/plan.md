# Implementation Plan: LLM Chat API

**Branch**: `001-llm-chat-api` | **Date**: 2026-04-28 |
**Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/001-llm-chat-api/spec.md`

## Summary

Build a minimal reviewer-ready FastAPI backend for the Pi School take-home:
email/password auth, JWT-protected SSE chat, OpenRouter-or-mock LLM provider
boundary, PostgreSQL-backed conversation history, Alembic migrations, deterministic
tests, Docker Compose, seed/smoke scripts, and concise documentation. The design
keeps routers thin, puts business logic in services, and uses PostgreSQL because
the assignment data has strict relational ownership constraints.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Uvicorn, SQLAlchemy 2.0 async, Alembic,
Pydantic Settings, PyJWT, pwdlib Argon2, httpx  
**Storage**: PostgreSQL 16 in Docker Compose; SQLite via aiosqlite for isolated
tests  
**Testing**: pytest, pytest-asyncio, pytest-cov, httpx ASGITransport, respx, Ruff  
**Target Platform**: Linux container and local developer machine  
**Project Type**: Single FastAPI web service  
**Performance Goals**: Stream first SSE token promptly with mock provider delays
of about 200 ms per chunk; live smoke completes in under 60 seconds after API
health  
**Constraints**: No real LLM calls in automated tests/CI; no secrets tracked; no
database transaction held during provider streaming; `.env.example` must be enough
for mock-provider local operation  
**Scale/Scope**: Take-home sized service: one API app, three database entities,
four core endpoints, docs and automation for local review

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Assignment-First Simplicity**: PASS. Scope is limited to assignment core plus
  small reviewer-value stretch items: logging, migrations, CI, seed, smoke.
- **Deterministic Quality Gates**: PASS. Tests mock OpenRouter and use SQLite;
  CI and smoke require no live provider key.
- **Secure Auth and Data Boundaries**: PASS. Argon2, JWT config, ownership
  checks, and redacted logging are explicit design requirements.
- **Streaming and Provider Isolation**: PASS. `LLMClient` interface and no DB
  transaction during stream are core architecture decisions.
- **Reviewer-Ready Local Operation**: PASS. Docker Compose, demo profile, smoke
  script, and no remote contributor automation are in scope.

## Project Structure

### Documentation (this feature)

```text
specs/001-llm-chat-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── main.py
├── config.py
├── database.py
├── deps.py
├── errors.py
├── logging.py
├── security.py
├── models.py
├── types.py
├── routers/
├── schemas/
└── services/

alembic/
├── env.py
├── script.py.mako
└── versions/

tests/
├── conftest.py
├── test_auth.py
├── test_chat.py
├── test_health.py
├── test_history.py
├── test_llm_provider.py
├── test_logging.py
├── test_models.py
└── test_user_journey.py

scripts/
├── seed.py
└── smoke.py

docs/
├── architecture.md
├── ci.md
├── local-dev.md
├── quickstart.md
├── scaffolding.md
└── testing.md
```

**Structure Decision**: Single-service layout at repository root. `app/routers`
owns HTTP concerns, `app/schemas` owns request/response validation, `app/services`
owns business logic and LLM provider integration, and `app/models.py` owns the
small relational schema.

## Complexity Tracking

No constitution violations. No complexity exceptions required.

## Phase 0: Research

Research is recorded in [research.md](./research.md). Decisions cover database,
streaming protocol, provider boundary, testing strategy, auth, logging, Docker,
and submission exclusions.

## Phase 1: Design and Contracts

Design artifacts:

- [data-model.md](./data-model.md)
- [contracts/openapi.yaml](./contracts/openapi.yaml)
- [quickstart.md](./quickstart.md)

Post-design constitution re-check:

- **Assignment-First Simplicity**: PASS. No frontend/RAG/Redis/Kubernetes.
- **Deterministic Quality Gates**: PASS. Tests and smoke are defined without
  secrets.
- **Secure Auth and Data Boundaries**: PASS. Ownership and logging rules are
  represented in data model and contracts.
- **Streaming and Provider Isolation**: PASS. Contracts define SSE event types;
  plan defines provider abstraction.
- **Reviewer-Ready Local Operation**: PASS. Quickstart includes Compose and demo
  profile, not remote submission.
