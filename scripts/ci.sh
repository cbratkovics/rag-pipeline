#!/usr/bin/env bash
set -euo pipefail

echo "Running quality checks..."
echo "========================"

# Track failures
FAILED=0

echo "1. Checking pip dependencies..."
if ! uv run python -m pip check; then
    echo "❌ Pip dependency check failed"
    FAILED=1
else
    echo "✓ Dependency check passed"
fi

echo ""
echo "2. Running ruff formatter..."
if ! uv run ruff format --check .; then
    echo "❌ Formatting check failed. Run: uv run ruff format ."
    FAILED=1
else
    echo "✓ Format check passed"
fi

echo ""
echo "3. Running ruff linter..."
if ! uv run ruff check .; then
    echo "❌ Linting failed. Run: uv run ruff check . --fix"
    FAILED=1
else
    echo "✓ Linting passed"
fi

echo ""
echo "4. Running mypy type checker..."
if ! uv run mypy src api --ignore-missing-imports; then
    echo "❌ Type checking failed"
    FAILED=1
else
    echo "✓ Type checking passed"
fi

echo ""
echo "5. Running pytest tests..."
if ! uv run pytest tests/ -m "not integration" -q; then
    echo "❌ Tests failed"
    FAILED=1
else
    echo "✓ Tests passed"
fi

echo ""
echo "========================"
if [ $FAILED -eq 0 ]; then
    echo "✅ All quality checks passed!"
    exit 0
else
    echo "❌ Some checks failed. Fix the issues above."
    exit 1
fi