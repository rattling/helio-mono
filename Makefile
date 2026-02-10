.PHONY: help setup install test lint format clean run status

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
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
	pytest tests/ -v

lint: ## Run linters
	ruff check .
	mypy services/ shared/

format: ## Format code
	black services/ shared/ tests/
	ruff check --fix .

clean: ## Clean generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/

run: ## Run the walking skeleton demonstration
	@echo "Running walking skeleton demonstration..."
	.venv/bin/python scripts/demo_walking_skeleton.py

telegram: ## Run Telegram bot
	@echo "Starting Telegram bot..."
	@if [ ! -f .env ]; then echo "Error: .env file not found. Run 'make setup' first."; exit 1; fi
	python scripts/run_telegram_bot.py

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
