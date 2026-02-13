.PHONY: help setup install test lint format precommit clean run demo telegram rebuild import-chatgpt view-events status deploy restart logs stop backup restore web-install web-run web-test web-build start-api start-web stop-api stop-web up down logs-api logs-web

# Default environment if not specified
ENV ?= dev
RUN_DIR ?= .run

ifeq ($(ENV),staging)
API_PORT_DEFAULT := 8001
UI_PORT_DEFAULT := 5174
else ifeq ($(ENV),live)
API_PORT_DEFAULT := 8002
UI_PORT_DEFAULT := 5175
else
API_PORT_DEFAULT := 8000
UI_PORT_DEFAULT := 5173
endif

API_PORT ?= $(API_PORT_DEFAULT)
UI_PORT ?= $(UI_PORT_DEFAULT)
API_BASE_URL ?= http://localhost:$(API_PORT)

API_PID_FILE := $(RUN_DIR)/api.$(ENV).pid
WEB_PID_FILE := $(RUN_DIR)/web.$(ENV).pid
API_LOG_FILE := $(RUN_DIR)/api.$(ENV).log
WEB_LOG_FILE := $(RUN_DIR)/web.$(ENV).log

help: ## Show this help message
	@echo 'Usage: make [target] [ENV=dev|staging|live]'
	@echo ''
	@echo 'Service Commands:'
	@echo '  make run [ENV=dev]       - Run Helionyx service locally (default: dev)'
	@echo '  make run ENV=staging     - Run service in staging mode'
	@echo '  make run ENV=live        - Run service in live mode'
	@echo '  make start-api ENV=dev   - Start API in background for env'
	@echo '  make start-web ENV=dev   - Start web UI in background for env'
	@echo '  make up ENV=dev          - Start API + web in background for env'
	@echo '  make down ENV=dev        - Stop API + web background processes for env'
	@echo '  make logs-api ENV=dev    - Tail local API log for env'
	@echo '  make logs-web ENV=dev    - Tail local web log for env'
	@echo ''
	@echo 'Deployment Commands (node1):'
	@echo '  make deploy ENV=<env>    - Deploy to node1 (ENV required: dev, staging, or live)'
	@echo '  make status [ENV=dev]    - Check local process/data status (default: dev)'
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

web-install: ## Install web dependencies
	cd web && npm install

web-run: ## Run web UI in foreground (ENV-aware API URL and port)
	cd web && VITE_API_BASE_URL=$(API_BASE_URL) npm run dev -- --host 0.0.0.0 --port $(UI_PORT)

web-test: ## Run web tests
	cd web && npm test

web-build: ## Build web UI bundle
	cd web && npm run build

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

precommit: ## Run pre-commit hooks (same checks as CI)
	.venv/bin/pre-commit run --all-files --show-diff-on-failure

clean: ## Clean generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/

run: ## Run Helionyx service (use ENV=dev|staging|live, default: dev)
	@echo "Starting Helionyx service (env: $(ENV))..."
	@if [ ! -f .env ]; then echo "Error: .env file not found. Run 'make setup' first."; exit 1; fi
	ENV=$(ENV) .venv/bin/python services/api/runner.py

start-api: ## Start API in background for ENV
	@mkdir -p $(RUN_DIR)
	@if [ -f $(API_PID_FILE) ] && kill -0 $$(cat $(API_PID_FILE)) 2>/dev/null; then \
		echo "API already running for $(ENV) (pid $$(cat $(API_PID_FILE)))"; \
		exit 0; \
	fi
	@rm -f $(API_PID_FILE)
	@echo "Starting API in background (env: $(ENV), port: $(API_PORT))"
	@ENV=$(ENV) API_PORT=$(API_PORT) nohup .venv/bin/python services/api/runner.py > $(API_LOG_FILE) 2>&1 & echo $$! > $(API_PID_FILE)
	@sleep 1
	@echo "API started: pid=$$(cat $(API_PID_FILE)) log=$(API_LOG_FILE)"

start-web: ## Start web UI in background for ENV
	@mkdir -p $(RUN_DIR)
	@if [ ! -d web/node_modules ]; then \
		echo "web/node_modules missing. Run 'make web-install' first."; \
		exit 1; \
	fi
	@if [ -f $(WEB_PID_FILE) ] && kill -0 $$(cat $(WEB_PID_FILE)) 2>/dev/null; then \
		echo "Web UI already running for $(ENV) (pid $$(cat $(WEB_PID_FILE)))"; \
		exit 0; \
	fi
	@rm -f $(WEB_PID_FILE)
	@echo "Starting web UI in background (env: $(ENV), port: $(UI_PORT), api: $(API_BASE_URL))"
	@VITE_API_BASE_URL=$(API_BASE_URL) nohup npm --prefix web run dev -- --host 0.0.0.0 --port $(UI_PORT) > $(WEB_LOG_FILE) 2>&1 & echo $$! > $(WEB_PID_FILE)
	@sleep 1
	@echo "Web UI started: pid=$$(cat $(WEB_PID_FILE)) log=$(WEB_LOG_FILE)"

stop-api: ## Stop background API for ENV
	@if [ -f $(API_PID_FILE) ]; then \
		PID=$$(cat $(API_PID_FILE)); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "Stopping API for $(ENV) (pid $$PID)"; \
			kill $$PID; \
		else \
			echo "Stale API pid file found for $(ENV); cleaning up"; \
		fi; \
		rm -f $(API_PID_FILE); \
	else \
		echo "No API pid file for $(ENV)"; \
	fi

stop-web: ## Stop background web UI for ENV
	@if [ -f $(WEB_PID_FILE) ]; then \
		PID=$$(cat $(WEB_PID_FILE)); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "Stopping web UI for $(ENV) (pid $$PID)"; \
			kill $$PID; \
		else \
			echo "Stale web pid file found for $(ENV); cleaning up"; \
		fi; \
		rm -f $(WEB_PID_FILE); \
	else \
		echo "No web pid file for $(ENV)"; \
	fi

up: ## Start API and web UI in background for ENV
	@$(MAKE) start-api ENV=$(ENV) API_PORT=$(API_PORT)
	@$(MAKE) start-web ENV=$(ENV) API_PORT=$(API_PORT) UI_PORT=$(UI_PORT) API_BASE_URL=$(API_BASE_URL)

down: ## Stop API and web UI background processes for ENV
	@$(MAKE) stop-web ENV=$(ENV)
	@$(MAKE) stop-api ENV=$(ENV)

logs-api: ## Tail local API log for ENV
	@if [ -f $(API_LOG_FILE) ]; then \
		tail -f $(API_LOG_FILE); \
	else \
		echo "No API log found at $(API_LOG_FILE)"; \
	fi

logs-web: ## Tail local web log for ENV
	@if [ -f $(WEB_LOG_FILE) ]; then \
		tail -f $(WEB_LOG_FILE); \
	else \
		echo "No web log found at $(WEB_LOG_FILE)"; \
	fi

demo: ## Run the walking skeleton demonstration
	@echo "Running walking skeleton demonstration..."
	.venv/bin/python scripts/demo_walking_skeleton.py

telegram: ## Run Telegram bot
	@echo "Starting Telegram bot..."
	@if [ ! -f .env ]; then echo "Error: .env file not found. Run 'make setup' first."; exit 1; fi
	.venv/bin/python scripts/run_telegram_bot.py

backup: ## Create a timestamped backup artifact (requires ENV=dev|staging|live)
	@ENV=$(ENV) ./scripts/backup.sh

restore: ## Restore from backup (requires ENV=dev|staging|live and BACKUP=<timestamp>)
	@if [ -z "$(BACKUP)" ]; then \
		echo "Error: BACKUP parameter required"; \
		echo "Usage: make restore ENV=$(ENV) BACKUP=20260211T120000Z"; \
		exit 1; \
	fi
	@ENV=$(ENV) BACKUP=$(BACKUP) ./scripts/restore.sh

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

status: ## Check local runtime status (processes, endpoints, data)
	@echo "=== Helionyx System Status ==="
	@echo "Environment: $(ENV)"
	@echo "API base URL: $(API_BASE_URL)"
	@echo "Web URL: http://localhost:$(UI_PORT)"
	@echo ""
	@if [ -d .venv ]; then \
		echo "✓ Virtual environment: .venv/"; \
	else \
		echo "✗ Virtual environment not found - run 'make install'"; \
	fi
	@if [ -d web/node_modules ]; then \
		echo "✓ Web dependencies installed"; \
	else \
		echo "✗ Web dependencies missing - run 'make web-install'"; \
	fi
	@echo ""
	@echo "Local process state:"
	@if [ -f $(API_PID_FILE) ] && kill -0 $$(cat $(API_PID_FILE)) 2>/dev/null; then \
		echo "  ✓ API running (pid $$(cat $(API_PID_FILE)))"; \
	else \
		echo "  ✗ API not running for $(ENV)"; \
	fi
	@if [ -f $(WEB_PID_FILE) ] && kill -0 $$(cat $(WEB_PID_FILE)) 2>/dev/null; then \
		echo "  ✓ Web UI running (pid $$(cat $(WEB_PID_FILE)))"; \
	else \
		echo "  ✗ Web UI not running for $(ENV)"; \
	fi
	@echo ""
	@echo "Endpoint probes:"
	@if command -v curl >/dev/null 2>&1; then \
		API_HEALTH=$$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 $(API_BASE_URL)/health || true); \
		API_READY=$$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 $(API_BASE_URL)/health/ready || true); \
		WEB_ROOT=$$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 http://localhost:$(UI_PORT) || true); \
		echo "  API /health      : $$API_HEALTH"; \
		echo "  API /health/ready: $$API_READY"; \
		echo "  Web /            : $$WEB_ROOT"; \
	else \
		echo "  curl not installed; skipping endpoint probes"; \
	fi
	@echo ""
	@if [ -f $(API_LOG_FILE) ]; then \
		echo "API log: $(API_LOG_FILE)"; \
	fi
	@if [ -f $(WEB_LOG_FILE) ]; then \
		echo "Web log: $(WEB_LOG_FILE)"; \
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
