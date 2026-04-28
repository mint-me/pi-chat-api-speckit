# CI

The pipeline has two jobs.

`quality` installs dependencies, applies Alembic migrations against Postgres,
runs Ruff, and executes the pytest suite with coverage.

`compose-smoke` builds the Docker stack, waits for `/health`, and runs
`scripts/smoke.py` against the live API.

This mirrors the reviewer workflow and keeps the automation deterministic.

