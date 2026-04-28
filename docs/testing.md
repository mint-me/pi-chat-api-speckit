# Testing

## Run Commands

```bash
make test
make coverage
make smoke
make test-docker
```

## Test Layers

1. Unit/service boundaries
   - auth helpers, model constraints, provider parsing
2. In-process API tests
   - `httpx.AsyncClient` + `ASGITransport`
   - real FastAPI app object
   - SQLite-backed deterministic fixtures
3. Live smoke test
   - `scripts/smoke.py` against running Docker Compose API
   - validates health, register, login, chat stream contract, history

## Determinism with Non-Deterministic LLMs

`scripts/smoke.py` validates the stream protocol (`token`/`done` events) and
history persistence, not exact text content. This keeps smoke useful for real
providers even when wording varies.

For deterministic automation (CI + local `make test`), OpenRouter is never used:
tests mock provider HTTP and/or rely on `MockClient`.

## Inspecting Stream Content During Smoke

To print live token chunks from SSE:

```bash
make smoke SMOKE_ARGS=--show-stream
```

To run smoke with the seeded demo user:

```bash
make smoke SMOKE_ARGS="--show-stream --use-demo-user"
```

To force the mock provider for Docker smoke, clear `OPENROUTER_API_KEY` in
`.env` and recreate the API container:

```bash
docker compose up -d --build --force-recreate api
make smoke
```

Setting `OPENROUTER_API_KEY= make smoke` only changes the environment of the
host-side smoke script. It does not change the environment already loaded by the
running API container.

To test live OpenRouter smoke, set these values in `.env` and recreate the API
container:

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openrouter/free
```

```bash
docker compose up -d --build --force-recreate api
make smoke
```

## Why `httpx.AsyncClient` Instead of Only FastAPI `TestClient`

This API is async end-to-end (DB + streaming). Async tests avoid sync wrappers
and keep behavior closer to production execution.

FastAPI references:
- https://fastapi.tiangolo.com/tutorial/testing/
- https://fastapi.tiangolo.com/advanced/async-tests/

Use the mock provider in automated tests. Never call OpenRouter live from CI.
