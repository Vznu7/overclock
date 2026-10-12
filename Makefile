.PHONY: help up down restart logs build test test-backend test-frontend lint format seed eval clean

SHELL := /bin/bash

help: ## Show available commands
	@echo "OVERCLOCK - Engineering Task Runner"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all local services via docker-compose (api, web, postgres, minio)
	docker compose -f infra/docker-compose.yml up -d

down: ## Stop all local services
	docker compose -f infra/docker-compose.yml down

restart: ## Restart local services
	docker compose -f infra/docker-compose.yml restart

logs: ## Follow docker-compose logs
	docker compose -f infra/docker-compose.yml logs -f

build: ## Rebuild container images
	docker compose -f infra/docker-compose.yml build

test: test-backend test-frontend ## Run all test suites

test-backend: ## Run backend unit and integration tests with coverage
	cd apps/api && uv run pytest --cov=app --cov-report=term-missing tests/

test-frontend: ## Run frontend unit tests
	cd apps/web && npm test -- --run

lint: ## Run code linters (ruff, mypy, eslint)
	cd apps/api && uv run ruff check app tests
	cd apps/api && uv run mypy app
	cd apps/web && npm run lint

format: ## Auto-format codebase
	cd apps/api && uv run ruff format app tests
	cd apps/web && npm run format

seed: ## Seed the database with fictional demo tenant data
	cd apps/api && uv run python -m seed.seed_demo_tenant

eval: ## Run AI PO extraction evaluation harness against synthetic golden POs
	cd apps/api && uv run python -m evals.run_evals

clean: ## Clean cache files, coverage reports and temporary test data
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf apps/api/.coverage apps/api/htmlcov apps/web/dist
