# Feature Specification: LLM Chat API

**Feature Branch**: `001-llm-chat-api`  
**Created**: 2026-04-28  
**Status**: Ready for Planning  
**Input**: User description: "Build a minimal LLM-powered FastAPI chat API with
email/password registration, JWT login, authenticated SSE streaming chat backed by
OpenRouter or a deterministic mock provider, persisted user conversation history,
PostgreSQL database schema with Alembic migrations, Docker Compose local
operation, deterministic tests, documentation, and no automatic remote submission
or interviewer invitations."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete Authenticated Chat Journey (Priority: P1)

A reviewer can register a new account, log in, send one message to the assistant,
receive streamed response chunks, and retrieve the persisted conversation history.

**Why this priority**: This is the assignment's core value path and proves the
four required endpoints work together.

**Independent Test**: Run a single end-to-end test that performs register, login,
streaming chat, and history retrieval against the in-process API.

**Acceptance Scenarios**:

1. **Given** a fresh database, **When** a user registers with a valid email and
   password, logs in, posts a chat message with a valid bearer token, and reads
   history, **Then** the system returns a token, streams at least one `token`
   event and one `done` event, and persists both user and assistant messages.
2. **Given** a request without a valid bearer token, **When** the user calls chat
   or history, **Then** the system rejects the request with an authentication
   error and does not persist messages.

---

### User Story 2 - Conversation Ownership and History (Priority: P2)

An authenticated user can list their own conversations and optionally retrieve a
specific conversation, while other users cannot discover or read it.

**Why this priority**: Conversation history is a required feature and ownership
boundaries are a core security requirement.

**Independent Test**: Create conversations for two users and verify ordering,
message order, empty history, and cross-user 404 behavior.

**Acceptance Scenarios**:

1. **Given** multiple conversations for one user, **When** the user requests
   history, **Then** conversations are returned newest-first and each message is
   returned oldest-first.
2. **Given** another user's conversation ID, **When** an authenticated user
   requests it, **Then** the system returns 404 and does not reveal ownership.

---

### User Story 3 - Local Reviewer Operation (Priority: P3)

A reviewer can start the API and database locally with Docker Compose, optionally
seed demo data, and run an automated smoke check without secrets.

**Why this priority**: The assignment states reviewers will first test
`docker-compose up`; this flow must be reliable before submission.

**Independent Test**: Start Compose from a clean database, wait for health, run
the smoke script, and verify the demo seed profile creates a login-ready account.

**Acceptance Scenarios**:

1. **Given** `.env.example` copied to `.env`, **When** a reviewer runs
   `docker compose up --build`, **Then** the API becomes healthy and the smoke
   script verifies health, register, login, streaming chat, and history.
2. **Given** a clean database, **When** a reviewer runs the demo profile, **Then**
   `demo@example.com` with `password123` exists with one sample conversation.

---

### User Story 4 - Optional Real LLM Provider (Priority: P4)

A candidate can provide an OpenRouter API key locally and receive streamed tokens
from the configured model without changing application code.

**Why this priority**: The assignment requires an LLM call, but automated checks
must remain deterministic and free of secrets.

**Independent Test**: Mock OpenRouter's streaming HTTP response in tests and
verify the parser emits content chunks and stops at `[DONE]`.

**Acceptance Scenarios**:

1. **Given** no `OPENROUTER_API_KEY`, **When** chat is called, **Then** the local
   mock provider streams deterministic chunks.
2. **Given** an `OPENROUTER_API_KEY`, **When** chat is called, **Then** the
   OpenRouter provider is selected and parses streaming `data:` events.

### Edge Cases

- Duplicate email registration returns a conflict and stores only one user.
- Email comparison is case-insensitive after normalization.
- Weak passwords and invalid emails fail request validation.
- Provider/network errors during streaming emit an SSE `error` event and avoid
  persisting a completed assistant message.
- Invalid conversation IDs and cross-user conversation IDs return 404.
- `.env` and real secrets are never tracked.
- Automated flows never invite contributors, push to remotes, or contact real
  interviewers.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose `POST /auth/register` accepting email and
  password and returning a created user without the password hash.
- **FR-002**: System MUST expose `POST /auth/login` accepting JSON email and
  password and returning a JWT bearer token for valid credentials.
- **FR-003**: System MUST protect `POST /chat` and `GET /chat/history` with JWT
  bearer authentication.
- **FR-004**: System MUST stream chat responses as Server-Sent Events with
  explicit `token`, `done`, and `error` event types.
- **FR-005**: System MUST persist users, conversations, and messages with
  ownership constraints and message roles.
- **FR-006**: System MUST let authenticated users retrieve only their own
  conversation history.
- **FR-007**: System MUST choose OpenRouter when `OPENROUTER_API_KEY` is set and
  a deterministic mock provider otherwise.
- **FR-008**: System MUST mock external provider HTTP in automated tests and CI.
- **FR-009**: System MUST provide Alembic migrations for the database schema.
- **FR-010**: System MUST provide Docker Compose services for API, PostgreSQL,
  test profile, and demo seed profile.
- **FR-011**: System MUST provide a smoke script that verifies the live API's
  health, auth, streaming chat, and history.
- **FR-012**: System MUST provide structured request logging with request IDs
  while excluding prompts, responses, passwords, tokens, and API keys.
- **FR-013**: System MUST document setup, design decisions, testing strategy,
  database choice, security notes, and future work.
- **FR-014**: System MUST NOT push code, create a remote repository, invite
  contributors, or contact interviewers automatically.

### Key Entities

- **User**: Registered account with normalized unique email, Argon2 password hash,
  and creation timestamp.
- **Conversation**: Chat thread owned by exactly one user, with title and updated
  timestamp for newest-first listing.
- **Message**: Ordered content within a conversation, with role `user` or
  `assistant`, provider metadata, and creation timestamp.
- **LLM Provider**: Runtime component that streams assistant text chunks from
  either OpenRouter or the local mock provider.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A clean local run completes the full smoke journey in under 60
  seconds after the API is healthy.
- **SC-002**: Automated tests cover the full user journey and pass without
  network access to real LLM providers.
- **SC-003**: Branch coverage is at least 80% for application code.
- **SC-004**: `docker compose up --build` reaches a healthy API state without
  manual database setup.
- **SC-005**: The repository contains no tracked `.env` file and no historical
  `.env` addition in the new local Git history.
- **SC-006**: A reviewer can identify the PostgreSQL rationale, LLM provider
  boundary, and testing strategy from README/docs in under five minutes.

## Assumptions

- The deliverable is a local Git repository only; remote publishing and
  collaborator invitations are manual and out of scope.
- PostgreSQL is used for the Compose runtime and SQLite is acceptable for fast,
  isolated automated tests.
- OpenRouter is the real provider target; a free model default is documented but
  no real API key is required for CI or smoke tests.
- The service has no frontend.
- Rate limiting, refresh tokens, RAG/vector search, GPU serving backends, and
  production telemetry are documented future work rather than core scope.
