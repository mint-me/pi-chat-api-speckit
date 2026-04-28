# Chat API

Minimal FastAPI chat service.
The app uses PostgreSQL, JWT auth, SSE streaming, Alembic migrations, and a
provider boundary that switches between OpenRouter and a deterministic mock.

## Quick Start

See [Quickstart](docs/quickstart.md) for the single source of truth.

## Documentation

- [Quickstart](docs/quickstart.md) - run the stack
- [Architecture](docs/architecture.md) - boundaries and design decisions
- [Local Dev](docs/local-dev.md) - local development workflow
- [Testing](docs/testing.md) - test layers and mocking strategy
- [CI](docs/ci.md) - automation strategy
- [Scaffolding](docs/scaffolding.md) - scaffold and rebuild flow

## Configuration

| Variable | Purpose |
| --- | --- |
| `ENVIRONMENT` | Runtime environment, usually `development` or `production` |
| `APP_NAME` | FastAPI application title |
| `COMPOSE_PROJECT_NAME` | Docker Compose project name used for container and volume names |
| `API_PORT` | Host port mapped to the API container |
| `POSTGRES_IMAGE` | Postgres image tag used by Compose |
| `POSTGRES_DB` | Database name created by the Postgres container |
| `POSTGRES_USER` | Least-privilege local database user created by the Postgres container |
| `POSTGRES_PASSWORD` | Password for `POSTGRES_USER`; change outside disposable local development |
| `POSTGRES_HOST` | Database host used by the app, usually `db` inside Compose |
| `POSTGRES_PORT` | Database port used in `DATABASE_URL` |
| `DATABASE_URL` | Async SQLAlchemy database URL for runtime |
| `TEST_DATABASE_URL` | Optional local test database URL |
| `JWT_SECRET_KEY` | Signing secret, minimum 32 characters |
| `JWT_ALGORITHM` | JWT algorithm, defaults to `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime |
| `OPENROUTER_API_KEY` | Enables OpenRouter instead of the mock provider |
| `OPENROUTER_MODEL` | OpenRouter chat model |
| `OPENROUTER_BASE_URL` | OpenRouter API base URL |

## API

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /chat`
- `GET /chat/history`

Interactive docs: `http://localhost:8000/docs`

If port 8000 is already in use locally, set `API_PORT=18000` for Compose and run
`make smoke BASE_URL=http://localhost:18000`.

Compose reads `.env` for interpolation and also passes it into the app
containers. Keep `DATABASE_URL` aligned with the `POSTGRES_*` values; if you
change database credentials after a Postgres volume already exists, recreate it
with `docker compose down -v`.

## Design Decisions

PostgreSQL matches the data shape here: users, conversations, and messages are
strictly relational, and foreign keys plus unique constraints add real value.

SSE is used for chat streaming because it keeps the protocol simple and is easy
to test end-to-end with FastAPI and httpx.

OpenRouter is optional. When the key is absent, the mock provider keeps tests
and local development deterministic.

JWT is used for stateless auth because this API needs a lightweight session
model and the protected routes are simple bearer-token endpoints.

## Testing

```bash
make test
make smoke
make test-docker
make clean
```

## Security Notes

- Never commit `.env`
- Passwords use Argon2 via `pwdlib`
- JWT secrets come from env and must be at least 32 characters
- Logs never include prompts, responses, or API keys

## Next Steps

- Rate limiting
- OpenTelemetry or Langfuse if observability needs grow
- Refresh tokens if the auth model expands
- RAG or Qdrant if the data shape changes
- GPU-backed provider implementations behind `LLMClient`

## AI Tools

This repository was built with AI-assisted coding. The codebase documents the
operational rules in `AGENTS.md`.
