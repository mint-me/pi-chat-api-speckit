# Quickstart: LLM Chat API

## Local Test Run

```bash
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

## Docker Reviewer Flow

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:8000/docs` or run the live smoke check:

```bash
python scripts/smoke.py http://localhost:8000
```

## Demo Seed Flow

```bash
docker compose down -v
docker compose --profile demo up --build
```

Demo credentials:

- Email: `demo@example.com`
- Password: `password123`

## Optional Real LLM

Add `OPENROUTER_API_KEY=...` to local `.env`, then restart Compose. Automated
tests and CI must still use mocked provider HTTP only.
