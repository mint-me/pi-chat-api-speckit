# Quick Start

This is the shortest path from a fresh clone to a working local stack.

## Prerequisites

- Docker and Docker Compose
- Python 3.12
- `uv`

Install `uv` if it is not already available:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version
```

## Run The Stack

```bash
cp .env.example .env
uv venv -p 3.12
source .venv/bin/activate
uv sync --dev

docker compose up -d --build
docker compose ps
```

The API should be available at:

- Health: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`

If port 8000 is already in use, edit `API_PORT` in `.env`, then use the same
port for smoke:

```bash
make smoke BASE_URL=http://localhost:18000
```

## Verify Locally

Seed the demo user, run pytest, then smoke the live HTTP stack:

```bash
make seed
make test
make smoke
```

Useful inspection commands:

```bash
docker compose logs -f
docker compose ps
```

The default `.env` leaves `OPENROUTER_API_KEY` empty. In that mode, the API uses
the deterministic mock provider, which is the expected baseline for local checks
and CI.

## Optional OpenRouter Provider

To test a live OpenRouter model, edit `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openrouter/free
```

Then recreate the API container so it reads the updated environment:

```bash
docker compose up -d --build --force-recreate api
make smoke
```

To verify that the container has the expected provider configuration without
printing the API key:

```bash
docker compose exec api sh -lc 'test -n "$OPENROUTER_API_KEY" && echo OPENROUTER_API_KEY=set'
docker compose exec api sh -lc 'echo "$OPENROUTER_MODEL"'
```

If live smoke fails with `provider_rate_limited`, OpenRouter accepted the
configuration but throttled the selected free model. Keep
`OPENROUTER_MODEL=openrouter/free`, wait for quota reset, add OpenRouter credits,
or clear `OPENROUTER_API_KEY` and recreate the API container to return to the
mock provider.

## Reset State

If you change Postgres credentials after a local database volume already exists,
recreate the volume:

```bash
docker compose down -v
docker compose up -d --build
```

To stop and remove local containers and volumes:

```bash
make docker-down
```

## Follow-Up Docs

- [Local Dev](local-dev.md) for non-Docker iteration loops
- [Testing](testing.md) for deterministic test strategy and FastAPI testing refs
- [Architecture](architecture.md) for service boundaries and data flow
- [CI](ci.md) for automation and environment variable handling
- [Scaffolding](scaffolding.md) for reconstruction steps
