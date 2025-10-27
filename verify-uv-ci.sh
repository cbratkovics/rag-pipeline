#!/bin/bash

# Verification script for UV-based CI/CD pipeline
# This script verifies that all CI commands work correctly with UV

set -e  # Exit on first error

echo "======================================"
echo "UV CI/CD Pipeline Verification Script"
echo "======================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command succeeds
check_command() {
    local description="$1"
    local command="$2"

    echo -n "Checking $description... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Command: $command"
        return 1
    fi
}

# Track overall status
all_passed=true

echo "1. Checking UV installation and lock file"
echo "==========================================="
check_command "UV is installed" "uv --version" || all_passed=false
check_command "uv.lock file exists" "test -f uv.lock" || all_passed=false
check_command "uv.lock is NOT in .gitignore" "! grep -q '^uv.lock$' .gitignore" || all_passed=false
echo ""

echo "2. Checking development tools installation"
echo "==========================================="
check_command "Ruff is available" "uv run ruff --version" || all_passed=false
check_command "MyPy is available" "uv run mypy --version" || all_passed=false
check_command "Pytest is available" "uv run pytest --version" || all_passed=false
check_command "Bandit is available" "uv run bandit --version" || all_passed=false
check_command "Pre-commit is available" "uv run pre-commit --version" || all_passed=false
echo ""

echo "3. Testing CI commands (as used in GitHub Actions)"
echo "==================================================="
check_command "Ruff format check" "uv run ruff format --check ." || all_passed=false
check_command "Ruff lint check" "uv run ruff check ." || all_passed=false
check_command "MyPy type check" "uv run mypy src api --ignore-missing-imports" || all_passed=false
# Note: Bandit may return non-zero exit code if security issues are found
# The CI uses continue-on-error: true for this step
echo -n "Checking Bandit security check... "
if uv run bandit -r src/ -ll > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASSED (no issues)${NC}"
else
    echo -e "${YELLOW}⚠ WARNING (security issues found - this is allowed)${NC}"
fi
check_command "Pytest collection" "CI=true uv run pytest tests/ -m 'not integration' --co -q" || all_passed=false
echo ""

echo "4. Checking Python project configuration"
echo "========================================="
check_command "pyproject.toml exists" "test -f pyproject.toml" || all_passed=false
check_command "Python 3.12+ required" "grep -q 'requires-python.*3.12' pyproject.toml" || all_passed=false
check_command "Project dependencies defined" "grep -q '^\[project\]' pyproject.toml && grep -q '^dependencies' pyproject.toml" || all_passed=false
check_command "Dev dependencies defined" "grep -q '^\[project.optional-dependencies\]' pyproject.toml" || all_passed=false
echo ""

echo "5. Checking GitHub Actions workflow"
echo "====================================="
check_command ".github/workflows/ci.yml exists" "test -f .github/workflows/ci.yml" || all_passed=false
echo ""

echo "6. Running quick smoke test"
echo "============================"
echo -e "${YELLOW}Running a subset of unit tests...${NC}"
if CI=true uv run pytest tests/test_rrf.py -v --tb=short; then
    echo -e "${GREEN}✓ Smoke test PASSED${NC}"
else
    echo -e "${RED}✗ Smoke test FAILED${NC}"
    all_passed=false
fi
echo ""

# Final summary
echo "======================================"
echo "VERIFICATION SUMMARY"
echo "======================================"
if $all_passed; then
    echo -e "${GREEN}✓ All checks PASSED!${NC}"
    echo ""
    echo "Your CI/CD pipeline is ready. To fix GitHub Actions:"
    echo "1. Stage and commit the changes:"
    echo "   git add uv.lock .gitignore pyproject.toml"
    echo "   git commit -m 'fix: update uv.lock and dependencies for CI/CD'"
    echo ""
    echo "2. Push to your branch:"
    echo "   git push"
    echo ""
    echo "The GitHub Actions workflow should now pass successfully."
    exit 0
else
    echo -e "${RED}✗ Some checks FAILED${NC}"
    echo ""
    echo "Please fix the issues above before committing."
    echo "Run 'uv sync --extra dev' to ensure all dependencies are installed."
    exit 1
fi