# Local Development

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

