#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Auto-fixing all issues..."

# Format code
echo "Formatting code..."
uv run ruff format .

# Fix linting issues
echo "Fixing linting issues..."
uv run ruff check . --fix

# Clear mypy cache
echo "Clearing mypy cache..."
rm -rf .mypy_cache

# Run mypy to check for remaining issues
echo "Checking types..."
uv run mypy src api --ignore-missing-imports || true

echo "✓ Auto-fix complete. Review changes before committing."