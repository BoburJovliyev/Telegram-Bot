.PHONY: help up down build logs migrate shell test lint format clean

# ==========================================
# Telegram Invite Tracker Bot — Makefile
# ==========================================

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==================== Docker Commands ====================

up: ## Start all services in detached mode
	docker compose up -d --build

down: ## Stop all services
	docker compose down

restart: ## Restart the bot container only
	docker compose restart bot

build: ## Build the bot Docker image without starting
	docker compose build bot

logs: ## Tail logs from the bot container
	docker compose logs -f bot

logs-all: ## Tail logs from all containers
	docker compose logs -f

ps: ## Show running containers
	docker compose ps

# ==================== Database Commands ====================

migrate: ## Run Alembic migrations (inside the container)
	docker compose exec bot alembic upgrade head

migrate-gen: ## Generate a new Alembic migration (usage: make migrate-gen MSG="add column")
	docker compose exec bot alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Downgrade the database by one revision
	docker compose exec bot alembic downgrade -1

migrate-history: ## Show migration history
	docker compose exec bot alembic history --verbose

# ==================== Development Commands ====================

shell: ## Open a Python shell inside the bot container
	docker compose exec bot python

test: ## Run tests locally
	pytest tests/ -v --tb=short

lint: ## Run linting (Ruff)
	ruff check src/ tests/

format: ## Format code (Black + Ruff)
	black src/ tests/
	ruff check --fix src/ tests/

typecheck: ## Run Mypy type checking
	mypy src/

# ==================== Cleanup ====================

clean: ## Remove all containers, volumes, and images
	docker compose down -v --rmi all
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
