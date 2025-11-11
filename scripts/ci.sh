#!/usr/bin/env bash
set -euo pipefail

echo "Running quality checks..."
echo "========================"

# Track failures
FAILED=0

echo "1. Checking pip dependencies..."
if ! uv run python -c "print('Dependencies OK')"; then
    echo "[FAIL] Pip dependency check failed"
    FAILED=1
else
    echo "[PASS] Dependency check passed"
fi

echo ""
echo "2. Running ruff formatter..."
if ! uv run ruff format --check .; then
    echo "[FAIL] Formatting check failed. Run: uv run ruff format ."
    FAILED=1
else
    echo "[PASS] Format check passed"
fi

echo ""
echo "3. Running ruff linter..."
if ! uv run ruff check .; then
    echo "[FAIL] Linting failed. Run: uv run ruff check . --fix"
    FAILED=1
else
    echo "[PASS] Linting passed"
fi

echo ""
echo "4. Running mypy type checker..."
if ! uv run mypy src api --ignore-missing-imports; then
    echo "[FAIL] Type checking failed"
    FAILED=1
else
    echo "[PASS] Type checking passed"
fi

echo ""
echo "5. Running pytest tests..."
if ! uv run pytest tests/ -m "not integration" -q; then
    echo "[FAIL] Tests failed"
    FAILED=1
else
    echo "[PASS] Tests passed"
fi

echo ""
echo "========================"
if [ $FAILED -eq 0 ]; then
    echo "[SUCCESS] All quality checks passed!"
    exit 0
else
    echo "[ERROR] Some checks failed. Fix the issues above."
    exit 1
fi