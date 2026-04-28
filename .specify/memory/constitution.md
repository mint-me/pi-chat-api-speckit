<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- [PRINCIPLE_1_NAME] -> I. Assignment-First Simplicity
- [PRINCIPLE_2_NAME] -> II. Deterministic Quality Gates
- [PRINCIPLE_3_NAME] -> III. Secure Auth and Data Boundaries
- [PRINCIPLE_4_NAME] -> IV. Streaming and Provider Isolation
- [PRINCIPLE_5_NAME] -> V. Reviewer-Ready Local Operation
Added sections:
- Technology and Scope Constraints
- Development Workflow and Evidence
Removed sections:
- None
Templates requiring updates:
- .specify/templates/plan-template.md: reviewed, no project-specific changes required
- .specify/templates/spec-template.md: reviewed, no project-specific changes required
- .specify/templates/tasks-template.md: reviewed, no project-specific changes required
Follow-up TODOs:
- None
-->

# Pi School Chat API Constitution

## Core Principles

### I. Assignment-First Simplicity
The project MUST satisfy the Pi School Step 2 assignment before adding optional
features. Core behavior is limited to FastAPI authentication, JWT-protected chat,
LLM streaming, persisted conversation history, Docker Compose operation, and clear
documentation. Optional additions MUST be justified by reviewer value and MUST NOT
obscure the baseline implementation.

Rationale: the assignment explicitly values simple, correct systems over complex
or impressive ones.

### II. Deterministic Quality Gates
Every committed implementation state MUST support deterministic local checks:
linting, format checking, migrations, and tests. External LLM calls MUST be mocked
or replaced by the local mock provider in automated tests and CI. At least one
end-to-end user journey test MUST exercise register, login, streaming chat, and
history retrieval together.

Rationale: reviewers must be able to verify behavior without secrets, paid APIs,
or timing-sensitive external services.

### III. Secure Auth and Data Boundaries
Passwords MUST be hashed with Argon2. JWT secrets MUST come from configuration and
be at least 32 characters. Protected endpoints MUST validate bearer tokens. Users
MUST only access their own conversations; cross-user resource reads MUST return
404 to avoid leaking existence. The application MUST never log prompts, responses,
passwords, tokens, API keys, or `.env` content.

Rationale: the smallest chat backend still handles credentials and private user
content, so security boundaries are part of the core feature rather than polish.

### IV. Streaming and Provider Isolation
The chat endpoint MUST stream responses as Server-Sent Events. User messages MUST
be persisted before the provider stream begins, assistant messages MUST be
persisted only after a successful stream, and no database transaction may be held
open across provider streaming. All LLM integrations MUST go through a small
provider interface so OpenRouter, local mock, or future serving backends can be
changed without modifying routers.

Rationale: this demonstrates ML-systems judgment while keeping the service easy to
explain and extend during a live walkthrough.

### V. Reviewer-Ready Local Operation
`docker compose up --build` MUST start a functional API and database without
manual setup beyond copying `.env.example` to `.env`. A demo seed path and a live
smoke script MUST be available, but the project MUST NOT push code, create remote
repositories, invite contributors, or contact real interviewers automatically.

Rationale: submission and collaborator invitations are intentionally manual, while
local verification must be frictionless.

## Technology and Scope Constraints

The implementation uses Python 3.12, FastAPI, SQLAlchemy 2.0 async, PostgreSQL in
Compose, SQLite for isolated tests, Alembic migrations, Pydantic v2 settings and
schemas, `httpx` for provider and smoke HTTP, `pytest`/`pytest-asyncio`/`respx` for
tests, and Ruff for linting and formatting. PostgreSQL is selected because the
assignment data is relational: users own conversations, conversations own
messages, and the ownership constraints belong in the schema.

The project explicitly excludes frontend code, RAG, Qdrant, Redis, Kubernetes,
refresh tokens, rate limiting, OpenTelemetry, Langfuse, live LLM calls in CI, and
automatic collaborator invitations.

## Development Workflow and Evidence

Work MUST follow the spec-kit flow: constitution, feature specification,
implementation plan, tasks, analysis/checklists where useful, and implementation.
Generated artifacts MUST remain in `specs/` and be consistent with the delivered
code. Tests SHOULD be written around public behavior and API contracts, not private
implementation details.

Each meaningful change SHOULD be committed with a Conventional Commit subject.
The README and docs MUST include setup instructions, design trade-offs, test
evidence, and an honest "What I'd do next" section.

## Governance

This constitution supersedes ad-hoc implementation preferences. Changes require a
documented amendment in this file, an updated version number, and a review of
spec, plan, task, README, and agent guidance consistency. Versioning follows
semantic rules: MAJOR for incompatible governance changes, MINOR for new or
materially expanded principles, PATCH for clarifications.

Before implementation is declared complete, the project MUST pass linting,
format-checking, tests with coverage threshold, Docker Compose health checks, the
live smoke script, and a secrets sanity check that confirms `.env` was never
tracked in the local repository history.

**Version**: 1.0.0 | **Ratified**: 2026-04-28 | **Last Amended**: 2026-04-28
