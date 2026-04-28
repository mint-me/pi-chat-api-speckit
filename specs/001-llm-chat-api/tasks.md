# Tasks: LLM Chat API

**Input**: Design documents from `specs/001-llm-chat-api/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required by constitution and specification. Test tasks appear before
their corresponding implementation work.

**Organization**: Tasks are grouped by user story to enable independently
testable increments.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label, e.g. `[US1]`
- Each task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize Python project, local venv, quality tools, and base files.

- [ ] T001 Initialize uv project and `.venv` in `.venv/`, `pyproject.toml`, and `uv.lock`
- [ ] T002 [P] Add repository ignores and Docker ignores in `.gitignore` and `.dockerignore`
- [ ] T003 [P] Configure Makefile commands in `Makefile`
- [ ] T004 [P] Add environment template in `.env.example`
- [ ] T005 [P] Create base package directories in `app/`, `tests/`, `scripts/`, `docs/`, and `alembic/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared app, database, auth, logging, and error handling required by
all user stories.

- [ ] T006 [P] Implement settings in `app/config.py`
- [ ] T007 [P] Implement database engine/session helpers in `app/database.py`
- [ ] T008 [P] Implement UUID type and SQLAlchemy entities in `app/types.py` and `app/models.py`
- [ ] T009 Add Alembic configuration and initial migration in `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, and `alembic/versions/0001_initial_schema.py`
- [ ] T010 [P] Implement error handling in `app/errors.py`
- [ ] T011 [P] Implement structured logging and request ID middleware in `app/logging.py`
- [ ] T012 [P] Implement password and JWT helpers in `app/security.py`
- [ ] T013 Implement dependency helpers in `app/deps.py`
- [ ] T014 Implement FastAPI app factory and router registration in `app/main.py`

**Checkpoint**: Foundation ready; user stories can start.

---

## Phase 3: User Story 1 - Complete Authenticated Chat Journey (Priority: P1) MVP

**Goal**: Register, login, stream chat, and retrieve persisted history.

**Independent Test**: `tests/test_user_journey.py` proves the full happy path.

### Tests for User Story 1

- [ ] T015 [P] [US1] Add health tests in `tests/test_health.py`
- [ ] T016 [P] [US1] Add registration/login tests in `tests/test_auth.py`
- [ ] T017 [P] [US1] Add streaming chat tests in `tests/test_chat.py`
- [ ] T018 [P] [US1] Add full journey test in `tests/test_user_journey.py`

### Implementation for User Story 1

- [ ] T019 [P] [US1] Implement auth schemas in `app/schemas/auth.py`
- [ ] T020 [P] [US1] Implement chat schemas in `app/schemas/chat.py`
- [ ] T021 [US1] Implement auth service in `app/services/auth_service.py`
- [ ] T022 [US1] Implement LLM provider boundary in `app/services/llm.py`
- [ ] T023 [US1] Implement chat service in `app/services/chat_service.py`
- [ ] T024 [US1] Implement health router in `app/routers/health.py`
- [ ] T025 [US1] Implement auth router in `app/routers/auth.py`
- [ ] T026 [US1] Implement chat router with SSE in `app/routers/chat.py`
- [ ] T027 [US1] Wire shared test fixtures in `tests/conftest.py`

**Checkpoint**: User Story 1 is fully functional and testable.

---

## Phase 4: User Story 2 - Conversation Ownership and History (Priority: P2)

**Goal**: Authenticated users can list own history and cannot access others.

**Independent Test**: `tests/test_history.py` verifies ownership, ordering, empty
history, and 404 for cross-user access.

### Tests for User Story 2

- [ ] T028 [P] [US2] Add model/schema tests in `tests/test_models.py`
- [ ] T029 [P] [US2] Add history ownership tests in `tests/test_history.py`

### Implementation for User Story 2

- [ ] T030 [US2] Complete history service behavior in `app/services/chat_service.py`
- [ ] T031 [US2] Complete history endpoint behavior in `app/routers/chat.py`

**Checkpoint**: User Story 2 works independently with protected history.

---

## Phase 5: User Story 3 - Local Reviewer Operation (Priority: P3)

**Goal**: Reviewer can run Compose, seed demo data, and smoke-test the live API.

**Independent Test**: `python scripts/smoke.py http://localhost:8000` after
Compose health.

### Tests for User Story 3

- [ ] T032 [P] [US3] Add smoke script in `scripts/smoke.py`

### Implementation for User Story 3

- [ ] T033 [US3] Add Dockerfile with non-root runtime in `Dockerfile`
- [ ] T034 [US3] Add Compose services, healthchecks, test profile, and demo profile in `docker-compose.yml`
- [ ] T035 [US3] Add idempotent demo seed script in `scripts/seed.py`

**Checkpoint**: User Story 3 is runnable from a clean local checkout.

---

## Phase 6: User Story 4 - Optional Real LLM Provider (Priority: P4)

**Goal**: OpenRouter can be selected by key while automation remains mocked.

**Independent Test**: `tests/test_llm_provider.py` mocks streaming HTTP and
verifies parser/provider selection.

### Tests for User Story 4

- [ ] T036 [P] [US4] Add provider tests in `tests/test_llm_provider.py`

### Implementation for User Story 4

- [ ] T037 [US4] Complete OpenRouter streaming parser and key-driven factory in `app/services/llm.py`

**Checkpoint**: Mock and OpenRouter provider paths are both covered.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, CI, coverage, and final validation.

- [ ] T038 [P] Add logging behavior tests in `tests/test_logging.py`
- [ ] T039 [P] Add CI workflow in `.github/workflows/ci.yml`
- [ ] T040 [P] Add README and docs in `README.md` and `docs/`
- [ ] T041 Add project guidance in `AGENTS.md` and `CLAUDE.md`
- [ ] T042 Run `uv run ruff check .` and `uv run ruff format --check .`
- [ ] T043 Run `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80`
- [ ] T044 Run Docker Compose health and smoke validation
- [ ] T045 Run secrets sanity checks for `.env`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup; blocks user stories.
- **US1 (Phase 3)**: Depends on Foundation; MVP.
- **US2 (Phase 4)**: Depends on Foundation and integrates with US1 persistence.
- **US3 (Phase 5)**: Depends on Foundation and US1 API contracts.
- **US4 (Phase 6)**: Depends on Foundation and LLM boundary from US1.
- **Polish (Phase 7)**: Depends on desired user stories.

### Parallel Opportunities

- T002-T005 can run in parallel after T001.
- T006-T012 can run in parallel, then T013-T014 complete foundation.
- Test files T015-T018 can be drafted in parallel.
- Docs, CI, and logging tests can run in parallel once implementation stabilizes.

## Implementation Strategy

### MVP First

1. Complete Setup and Foundation.
2. Complete US1 and verify `tests/test_user_journey.py`.
3. Add US2 ownership and history hardening.
4. Add Docker/seed/smoke for reviewer operation.
5. Add OpenRouter mocked provider coverage and documentation.

### Notes

- Mark each completed task as `[X]`.
- Do not create remotes, push, or invite contributors.
- Keep automated tests deterministic and secret-free.
