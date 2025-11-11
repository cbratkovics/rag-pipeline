#!/usr/bin/env bash
set -euo pipefail

echo "==================================="
echo "VALIDATING CI/CD PIPELINE"
echo "==================================="
echo ""

echo "[INFO] Running validation checks..."
echo "----------------------------"

echo ""
echo "1. Checking uv environment..."
uv run python -m pip check
echo "[PASS] Environment check passed"

echo ""
echo "2. Running ruff formatter check..."
uv run ruff format --check .
echo "[PASS] Format check passed"

echo ""
echo "3. Running ruff linter..."
uv run ruff check .
echo "[PASS] Linting passed"

echo ""
echo "4. Running mypy type checker..."
uv run mypy src api --ignore-missing-imports
echo "[PASS] Type checking passed"

echo ""
echo "5. Running unit tests..."
uv run pytest tests/ -m "not integration" -q
echo "[PASS] Tests passed"

echo ""
echo "==================================="
echo "[SUCCESS] ALL VALIDATION CHECKS PASSED!"
echo "==================================="
echo ""
echo "Pre-commit hooks status:"
pre-commit --version
echo ""
echo "To verify hooks work, run: pre-commit run --all-files"
echo ""
echo "CI/CD Pipeline Components:"
echo "- Pre-commit hooks prevent bad commits"
echo "- MyPy type checking enforced"
echo "- Ruff formatting enforced"
echo "- Ruff linting enforced"
echo "- Unit tests validated"
echo ""
echo "Pipeline is ready for GitHub Actions!"