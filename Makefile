DEFAULT: help

.PHONY: help
help:
	@grep -E -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: checks
checks: ## Run linting etc
checks:
	uv run ruff check tests pygoodwe
	uv run ty check tests pygoodwe
	uv run mypy --strict tests pygoodwe
	uv run pytest

.PHONY: coverage
coverage: ## Run tests with coverage
coverage:
	uv run coveralls

.PHONY: docs
docs: ## Build the documentation
docs:
	uv run mkdocs build


.PHONY: docs_serve
docs_serve: ## Serve the documentation locally
docs_serve:
	uv run mkdocs serve --livereload