#!/usr/bin/env bash
set -euo pipefail

echo "Running quality checks..."
echo "========================"

# Track failures
FAILED=0

echo "1. Checking Poetry lock file..."
if ! poetry check; then
    echo "❌ Poetry check failed"
    FAILED=1
else
    echo "✓ Poetry check passed"
fi

echo ""
echo "2. Running ruff formatter..."
if ! poetry run ruff format --check .; then
    echo "❌ Formatting check failed. Run: poetry run ruff format ."
    FAILED=1
else
    echo "✓ Format check passed"
fi

echo ""
echo "3. Running ruff linter..."
if ! poetry run ruff check .; then
    echo "❌ Linting failed. Run: poetry run ruff check . --fix"
    FAILED=1
else
    echo "✓ Linting passed"
fi

echo ""
echo "4. Running mypy type checker..."
if ! poetry run mypy src api --ignore-missing-imports; then
    echo "❌ Type checking failed"
    FAILED=1
else
    echo "✓ Type checking passed"
fi

echo ""
echo "5. Running pytest tests..."
if ! poetry run pytest tests/ -m "not integration" -q; then
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