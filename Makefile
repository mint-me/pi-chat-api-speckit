.DEFAULT_GOAL := help
BASE_URL ?= http://localhost:8000

.PHONY: help install run migrate test coverage lint format format-check smoke demo docker-up docker-down test-docker

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync --dev

run: ## Start the API with reload
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate: ## Apply Alembic migrations
	uv run alembic upgrade head

test: ## Run the test suite
	uv run pytest -q

coverage: ## Run tests with coverage
	uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80

lint: ## Run Ruff checks
	uv run ruff check .

format: ## Format the code
	uv run ruff format .

format-check: ## Check formatting
	uv run ruff format --check .

smoke: ## Run the live HTTP smoke test
	uv run python scripts/smoke.py $(BASE_URL)

demo: ## Start Compose and seed demo data
	docker compose --profile demo up --build

docker-up: ## Build and start Compose
	docker compose up --build

docker-down: ## Stop and remove Compose containers and volumes
	docker compose down -v

test-docker: ## Run pytest inside the Compose test container
	docker compose --profile test run --rm test
