DEFAULT: help

.PHONY: help
help:
	@grep -E -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: checks
checks: ## Run linting etc
checks:
	poetry run pytest
	poetry run ruff tests pygoodwe
	poetry run mypy --strict tests pygoodwe

.PHONY: coverage
coverage: ## Run tests with coverage
coverage:
	poetry run pytest --cov-report html --cov=pygoodwe tests