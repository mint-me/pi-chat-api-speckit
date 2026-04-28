# Local Development

## Setup

### Install `uv`

`uv` is a fast Python package installer and resolver. Install it once:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via package managers
# macOS: brew install uv
# Linux: apt install uv  # (if available)

# Verify installation
uv --version
```

See [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) for details.

### Create and activate a venv

```bash
# Create a venv for this project (Python 3.12 is pinned in pyproject.toml)
uv venv

# Activate the venv
source .venv/bin/activate    # macOS / Linux
# or
.venv\Scripts\activate       # Windows

# Sync dependencies from pyproject.toml + uv.lock
uv sync --dev

# Verify: you should see `(.venv)` in your shell prompt
```

---

## Why `uv` (not `pip`/`requirements.txt`)

`uv` is used for dependency and Python runtime management because it gives:

- **deterministic builds**: `uv.lock` pins exact versions and hashes
- **fast syncs**: installs only changed packages via `uv sync --dev`
- **single command for all ops**: `uv run <cmd>` works inside or outside a venv
- **built-in Python management**: `uv python install 3.12` manages Python versions

This project uses `pyproject.toml` (modern Python standard, PEP 517/518) instead
of `requirements.txt` (legacy). There is no `requirements.txt` because `uv` reads
directly from `pyproject.toml` and `uv.lock`.

If you need a `requirements.txt` for external tools (e.g., other CI systems),
you can generate one:

```bash
uv pip compile pyproject.toml -o requirements.txt
```

### Common `uv` commands

```bash
uv sync --dev              # Install dependencies (dev + prod)
uv sync                    # Install only production dependencies
uv run <command>           # Run a command inside the venv (auto-activates)
uv run alembic upgrade head
uv run ruff check .
uv run ruff format .
uv run pytest -q
```

Start the API against a running Postgres instance:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Quick Start

The default local workflow uses `.env` copied from `.env.example`:

```bash
cp .env.example .env
uv sync --dev
uv run alembic upgrade head
make db-reset
make seed
uv run uvicorn app.main:app --reload
```

Reset database and seed demo data:

```bash
make db-reset
make seed
```
