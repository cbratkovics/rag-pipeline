#!/usr/bin/env bash
set -euo pipefail

echo "Running quality checks..."
echo "========================"

echo "1. Running ruff linter..."
poetry run ruff check .

echo ""
echo "2. Running mypy type checker..."
poetry run mypy src api

echo ""
echo "3. Running pytest tests..."
poetry run pytest -q

echo ""
echo "========================"
echo "All quality checks passed!"