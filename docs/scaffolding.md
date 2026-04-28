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

