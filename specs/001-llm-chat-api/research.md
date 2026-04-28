# Research: LLM Chat API

## Decision: Use PostgreSQL for runtime storage

**Rationale**: The data is relational: users own conversations, conversations own
messages, and ownership must be enforced by foreign keys and cascades. PostgreSQL
also aligns with the assignment's relational database evaluation and enables
Alembic migrations. JSONB remains available for provider metadata.

**Alternatives considered**: MongoDB would fit variable-shape RAG metadata but is
less direct for this strict three-entity topology. SQLite is useful for tests but
does not represent the reviewer runtime.

## Decision: Use Server-Sent Events for streaming

**Rationale**: SSE is sufficient for one-way assistant token streaming and works
well with HTTP clients, FastAPI `StreamingResponse`, and simple smoke tests.

**Alternatives considered**: WebSocket adds bidirectional complexity not required
by the assignment. Long polling violates token-as-generated streaming.

## Decision: Key-driven LLM provider selection

**Rationale**: If `OPENROUTER_API_KEY` exists, use OpenRouter; otherwise use the
deterministic local mock. This removes a provider enum and gives reviewers a
working default while letting the candidate manually test real inference.

**Alternatives considered**: A required provider enum adds configuration branches
and reviewer friction. A mock-only implementation would need stronger assignment
justification and provide less ML-systems signal.

## Decision: Keep LLM integration behind `LLMClient`

**Rationale**: A small streaming interface isolates routers and services from
OpenRouter HTTP details. Future BentoML, vLLM, RunPod, or Triton clients can slot
behind the same boundary.

**Alternatives considered**: Calling OpenRouter directly in the router is shorter
but tightly couples HTTP routing, persistence, and provider behavior.

## Decision: Use JWT bearer tokens and Argon2 password hashing

**Rationale**: JWT bearer auth satisfies the assignment and keeps protected routes
stateless. Argon2 via `pwdlib` gives modern password hashing with minimal code.

**Alternatives considered**: Sessions require server-side storage not requested.
SHA-256/MD5 password hashing is unacceptable.

## Decision: Test with httpx ASGITransport, SQLite, and respx

**Rationale**: In-process FastAPI tests are fast and deterministic. SQLite allows
fresh schemas per test. `respx` mocks OpenRouter HTTP streaming without secrets or
network dependency.

**Alternatives considered**: Live provider tests are flaky and require secrets.
Only container smoke tests would make debugging slower and reduce edge coverage.

## Decision: Use stdlib structured JSON logging

**Rationale**: Request IDs and JSON logs improve walkthrough/debugging value
without pulling in production telemetry. Logs must omit prompts, responses, and
secrets.

**Alternatives considered**: OpenTelemetry/Langfuse is useful future work but
over-scoped for this take-home.

## Decision: Docker Compose with demo and test profiles

**Rationale**: The assignment says reviewers will test Compose first. Profiles
keep normal API startup, seeded demo data, and containerized tests separate.

**Alternatives considered**: Shell-only setup is less reviewer-proof. A single
profile for both seed and tests conflates different workflows.
