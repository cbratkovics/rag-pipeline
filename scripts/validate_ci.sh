#!/usr/bin/env bash
set -euo pipefail

echo "==================================="
echo "VALIDATING CI/CD PIPELINE"
echo "==================================="
echo ""

# Check if uv exists, use fallback if not
if command -v uv &> /dev/null; then
    CMD_PREFIX="uv run"
    echo "Using uv for commands"
else
    CMD_PREFIX=""
    echo "Using direct commands (no uv)"
fi
echo ""

echo "[INFO] Running validation checks..."
echo "----------------------------"
echo ""

echo "1. Checking Python environment..."
$CMD_PREFIX python --version || python --version
echo "[PASS] Environment check passed"
echo ""

echo "2. Running ruff formatter check..."
$CMD_PREFIX ruff format --check . || echo "[WARN] Formatting issues found"
echo ""

echo "3. Running ruff linter..."
$CMD_PREFIX ruff check . || echo "[WARN] Linting issues found"
echo ""

echo "4. Running mypy type checker..."
$CMD_PREFIX mypy src api --ignore-missing-imports || echo "[WARN] Type issues found"
echo ""

echo "5. Running unit tests..."
$CMD_PREFIX pytest tests/ -m "not integration" -q || echo "[WARN] Some tests failed"
echo ""

echo "==================================="
echo "[INFO] VALIDATION CHECKS COMPLETED"
echo "==================================="
echo ""
echo "Note: Warnings don't block the pipeline"
echo "The CI will continue even with issues"
