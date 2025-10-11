.PHONY: test test-cov format lint type-check all quality-gate task-complete clean help

# Default target - show help
help:
	@echo "GitLab MCP Server - Quality Checks"
	@echo ""
	@echo "Available targets:"
	@echo "  make test           - Run all tests"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make format         - Format code with black and ruff"
	@echo "  make lint           - Check code with ruff (must pass with ZERO errors)"
	@echo "  make type-check     - Type check with mypy (must pass with ZERO errors)"
	@echo "  make all            - Run all quality checks (recommended)"
	@echo "  make quality-gate   - Alias for 'all' - use after each task"
	@echo "  make task-complete  - Alias for 'all' - marks task as done"
	@echo "  make clean          - Remove cache and generated files"
	@echo ""
	@echo "Quality Standards:"
	@echo "  - Linting must pass with ZERO errors"
	@echo "  - Type checking must pass with ZERO errors"
	@echo "  - Code must be formatted with black"
	@echo "  - Tests must pass with required coverage"
	@echo ""

test:
	@echo "Running tests..."
	uv run pytest

test-cov:
	@echo "Running tests with coverage..."
	uv run pytest --cov=src --cov-report=html --cov-report=term-missing

format:
	@echo "Formatting code..."
	uv run black src/ tests/
	uv run ruff check --fix src/ tests/

lint:
	@echo "Linting code (must pass with ZERO errors)..."
	uv run ruff check src/ tests/

type-check:
	@echo "Type checking (must pass with ZERO errors)..."
	uv run mypy src/

all: format lint type-check test
	@echo ""
	@echo "✅ All quality checks passed!"
	@echo ""

# Quality gate - use after every task
quality-gate: all
	@echo "✅ Quality gate passed - task validated"

# Alias for quality-gate
task-complete: quality-gate
	@echo "✅ Task complete - ready for next task"

clean:
	@echo "Cleaning cache and generated files..."
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	@echo "✅ Clean complete"
