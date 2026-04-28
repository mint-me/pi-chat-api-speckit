# CI

The pipeline has two jobs.

`quality` installs dependencies, applies Alembic migrations against Postgres,
runs Ruff, and executes the pytest suite with coverage.

`compose-smoke` builds the Docker stack, waits for `/health`, and runs
`scripts/smoke.py` against the live API.

This mirrors local runtime workflow and keeps automation deterministic.

## Secrets and Env Strategy

The default CI path does not require paid provider secrets. It uses the mock
LLM path by keeping `OPENROUTER_API_KEY` unset.

Values handled in CI:

- `DATABASE_URL`: set from the local Postgres service in the workflow
- `JWT_SECRET_KEY`: loaded from `secrets.JWT_SECRET_KEY` when available, else a
  deterministic CI-safe fallback value
- `OPENROUTER_API_KEY`: optional; not required for base checks

The Compose smoke job copies `.env.example` to `.env`, so every variable needed
by `docker-compose.yml` must be present in `.env.example`. Keep Compose-only
values such as `COMPOSE_PROJECT_NAME`, `API_PORT`, and `POSTGRES_*` documented
there instead of hardcoding them in the Compose file.

For optional provider integration checks, add repository secret
`OPENROUTER_API_KEY` and gate those checks behind secret presence.
