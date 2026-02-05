.PHONY: check
check:
	uv run ruff check --fix
	uv run ruff format
	uv run pyright

.PHONY: test
test:
	uv run pytest

.PHONY: cov
cov:
	uv run pytest --cov=inspect_harbor --cov-report=html --cov-branch

.PHONY: install
install:
	uv sync
	pre-commit install

.PHONY: clean
clean:
	rm -rf .pytest_cache htmlcov .coverage *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
