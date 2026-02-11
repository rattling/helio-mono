.PHONY: help setup install test lint format clean run demo telegram rebuild import-chatgpt view-events status deploy restart logs stop

# Default environment if not specified
ENV ?= dev

help: ## Show this help message
	@echo 'Usage: make [target] [ENV=dev|staging|live]'
	@echo ''
	@echo 'Service Commands:'
	@echo '  make run [ENV=dev]       - Run Helionyx service locally (default: dev)'
	@echo '  make run ENV=staging     - Run service in staging mode'
	@echo '  make run ENV=live        - Run service in live mode'
	@echo ''
	@echo 'Deployment Commands (node1):'
	@echo '  make deploy ENV=<env>    - Deploy to node1 (ENV required: dev, staging, or live)'
	@echo '  make status [ENV=dev]    - Check deployment status (default: dev)'
	@echo '  make restart ENV=<env>   - Restart deployed service (ENV required)'
	@echo '  make logs ENV=<env>      - View service logs (ENV required)'
	@echo '  make stop ENV=<env>      - Stop deployed service (ENV required)'
	@echo ''
	@echo 'Other Commands:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup (create .env, directories)
	@echo "Setting up Helionyx..."
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env file - please edit with your values"; fi
	@mkdir -p data/events data/projections
	@echo "Setup complete! Run 'make install' next."

install: ## Install dependencies
	@echo "Installing dependencies..."
	pip install -e ".[dev,extraction,telegram]"
	@echo "Dependencies installed!"

test: ## Run tests
	.venv/bin/python -m pytest tests/ -v

test-cov: ## Run tests with coverage
	.venv/bin/python -m pytest tests/ --cov=services --cov=shared --cov-report=html --cov-report=term

lint: ## Run linters
	.venv/bin/ruff check services/ shared/ tests/
	.venv/bin/mypy services/ shared/ || echo "mypy completed with warnings"

format: ## Format code
	.venv/bin/black services/ shared/ tests/
	.venv/bin/ruff check --fix services/ shared/ tests/

clean: ## Clean generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/

run: ## Run Helionyx service (use ENV=dev|staging|live, default: dev)
	@echo "Starting Helionyx service (env: $(ENV))..."
	@if [ ! -f .env ]; then echo "Error: .env file not found. Run 'make setup' first."; exit 1; fi
	ENV=$(ENV) .venv/bin/python services/api/runner.py

demo: ## Run the walking skeleton demonstration
	@echo "Running walking skeleton demonstration..."
	.venv/bin/python scripts/demo_walking_skeleton.py

telegram: ## Run Telegram bot
	@echo "Starting Telegram bot..."
	@if [ ! -f .env ]; then echo "Error: .env file not found. Run 'make setup' first."; exit 1; fi
	.venv/bin/python scripts/run_telegram_bot.py

rebuild: ## Rebuild projections from event log
	@echo "Rebuilding projections from event log..."
	.venv/bin/python scripts/rebuild_projections.py

import-chatgpt: ## Import ChatGPT conversation history (pass FILE=path/to/conversations.json)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE parameter required."; \
		echo "Usage: make import-chatgpt FILE=path/to/conversations.json"; \
		exit 1; \
	fi
	@echo "Importing ChatGPT conversation history from $(FILE)..."
	.venv/bin/python scripts/import_chatgpt.py $(FILE)

view-events: ## View recent events from the event log
	@echo "Recent events from event log:"
	.venv/bin/python scripts/view_events.py

status: ## Check system status and event log
	@echo "=== Helionyx System Status ==="
	@echo ""
	@if [ -d .venv ]; then \
		echo "✓ Virtual environment: .venv/"; \
	else \
		echo "✗ Virtual environment not found - run 'make install'"; \
	fi
	@echo ""
	@if [ -d data/events ]; then \
		echo "Event Log Status:"; \
		ls -lh data/events/ 2>/dev/null || echo "  No event files yet"; \
		echo ""; \
		echo "Total events:"; \
		wc -l data/events/*.jsonl 2>/dev/null | tail -1 || echo "  0 events"; \
	else \
		echo "Event log directory not yet created"; \
	fi
	@echo ""

# Deployment commands (for node1 deployment)

deploy: ## Deploy to node1 (requires ENV=dev|staging|live)
	@if [ -z "$(ENV)" ]; then \
		echo "Error: ENV parameter required"; \
		echo "Usage: make deploy ENV=dev|staging|live"; \
		exit 1; \
	fi
	@./scripts/deploy/deploy.sh $(ENV)

restart: ## Restart deployed service (requires ENV=dev|staging|live)
	@if [ -z "$(ENV)" ]; then \
		echo "Error: ENV parameter required"; \
		echo "Usage: make restart ENV=dev|staging|live"; \
		exit 1; \
	fi
	@./scripts/deploy/restart.sh $(ENV)

logs: ## View service logs (requires ENV=dev|staging|live)
	@if [ -z "$(ENV)" ]; then \
		echo "Error: ENV parameter required"; \
		echo "Usage: make logs ENV=dev|staging|live"; \
		exit 1; \
	fi
	@./scripts/deploy/logs.sh $(ENV)

stop: ## Stop deployed service (requires ENV=dev|staging|live)
	@if [ -z "$(ENV)" ]; then \
		echo "Error: ENV parameter required"; \
		echo "Usage: make stop ENV=dev|staging|live"; \
		exit 1; \
	fi
	@./scripts/deploy/stop.sh $(ENV)
