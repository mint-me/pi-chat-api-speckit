# Quick Start

Clone the repo, copy the sample env file, and start the stack:

```bash
cp .env.example .env
docker compose up --build
make smoke
```

If port 8000 is already in use, run Compose with `API_PORT=18000` and smoke with
`uv run python scripts/smoke.py http://localhost:18000`.

For a seeded demo account:

```bash
docker compose --profile demo up --build
```

The demo profile seeds `demo@example.com` with `password123` and one sample
conversation.

If you set `OPENROUTER_API_KEY` in `.env`, the live provider is used. If the
key is absent, the deterministic mock provider is used instead.

To run smoke using the default seeded account:

```bash
make smoke SMOKE_ARGS="--show-stream --use-demo-user"
```

## Follow-Up Docs

- [Local Dev](local-dev.md) for non-Docker iteration loops
- [Testing](testing.md) for deterministic test strategy and FastAPI testing refs
- [Architecture](architecture.md) for service boundaries and data flow
- [CI](ci.md) for automation and environment variable handling
- [Scaffolding](scaffolding.md) for reconstruction steps
