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
	pip install -e ".[dev,extraction]"
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

run: ## Run the walking skeleton (to be implemented)
	@echo "Walking skeleton not yet implemented (see issue #3)"

status: ## Check system status (to be implemented)
	@echo "Status check not yet implemented (see issue #5)"
