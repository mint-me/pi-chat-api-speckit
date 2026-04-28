# Local Development

## Why `uv`

`uv` is used for dependency and Python runtime management because it gives:

- deterministic installs from `uv.lock`
- fast environment syncs (`uv sync --dev`)
- consistent local/CI command execution (`uv run ...`)

Scope in this project: install dependencies, run migrations, run lint/tests,
and execute local scripts.

```bash
uv sync --dev
uv run alembic upgrade head
uv run ruff check .
uv run ruff format .
uv run pytest -q
```

Start the API against a running Postgres instance:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The default local workflow uses `.env` copied from `.env.example`.

Reset database and seed demo data:

```bash
make db-reset
make seed
```
