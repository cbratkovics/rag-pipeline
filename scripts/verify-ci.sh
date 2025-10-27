#!/usr/bin/env bash
# Verify CI/CD setup is correctly configured
set -euo pipefail

echo "======================================"
echo "CI/CD Configuration Verification"
echo "======================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ISSUES_FOUND=0

# Check 1: uv.lock exists
echo "Checking for uv.lock file..."
if [ -f "uv.lock" ]; then
    echo -e "${GREEN}✓${NC} uv.lock exists"
    
    # Check if it's in git
    if git ls-files --error-unmatch uv.lock > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} uv.lock is tracked in git"
    else
        echo -e "${YELLOW}⚠${NC}  uv.lock is not committed to git"
        echo "   Run: git add uv.lock && git commit -m 'Add uv.lock'"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
else
    echo -e "${RED}✗${NC} uv.lock not found!"
    echo "   Run: ./scripts/generate-lock.sh"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""

# Check 2: Pre-commit config
echo "Checking pre-commit configuration..."
if [ -f ".pre-commit-config.yaml" ]; then
    # Check if it uses uv run instead of .venv/bin/
    if grep -q ".venv/bin/" .pre-commit-config.yaml; then
        echo -e "${RED}✗${NC} Pre-commit hooks still use .venv/bin/"
        echo "   Update .pre-commit-config.yaml to use 'uv run' instead"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    else
        echo -e "${GREEN}✓${NC} Pre-commit hooks correctly use 'uv run'"
    fi
else
    echo -e "${YELLOW}⚠${NC}  No .pre-commit-config.yaml found"
fi

echo ""

# Check 3: CI workflow
echo "Checking GitHub Actions workflow..."
if [ -f ".github/workflows/ci.yml" ]; then
    # Check for uv installation
    if grep -q "astral-sh/setup-uv" .github/workflows/ci.yml; then
        echo -e "${GREEN}✓${NC} CI workflow installs uv"
    else
        echo -e "${RED}✗${NC} CI workflow doesn't install uv"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
    
    # Check for uv sync --frozen
    if grep -q "uv sync --frozen" .github/workflows/ci.yml; then
        echo -e "${GREEN}✓${NC} CI workflow uses 'uv sync --frozen'"
    else
        echo -e "${YELLOW}⚠${NC}  CI workflow doesn't use 'uv sync --frozen'"
    fi
else
    echo -e "${RED}✗${NC} No CI workflow found at .github/workflows/ci.yml"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""

# Check 4: Python version
echo "Checking Python version..."
if [ -f "pyproject.toml" ]; then
    if grep -q 'python = "^3.12"' pyproject.toml; then
        echo -e "${GREEN}✓${NC} pyproject.toml specifies Python 3.12"
    else
        echo -e "${YELLOW}⚠${NC}  pyproject.toml doesn't specify Python 3.12"
    fi
fi

if [ -f ".python-version" ]; then
    PYTHON_VERSION=$(cat .python-version)
    if [[ "$PYTHON_VERSION" == "3.12"* ]]; then
        echo -e "${GREEN}✓${NC} .python-version specifies Python 3.12"
    else
        echo -e "${YELLOW}⚠${NC}  .python-version specifies Python $PYTHON_VERSION"
    fi
else
    echo -e "${YELLOW}⚠${NC}  No .python-version file found"
fi

echo ""

# Check 5: Test uv commands
echo "Testing uv commands..."
export PATH="$HOME/.local/bin:$PATH"

if command -v uv &> /dev/null; then
    echo -e "${GREEN}✓${NC} uv is installed: $(uv --version)"
    
    # Test ruff
    if uv run ruff --version > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} 'uv run ruff' works"
    else
        echo -e "${RED}✗${NC} 'uv run ruff' failed"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
    
    # Test pytest
    if uv run pytest --version > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} 'uv run pytest' works"
    else
        echo -e "${RED}✗${NC} 'uv run pytest' failed"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
else
    echo -e "${RED}✗${NC} uv is not installed or not in PATH"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""

# Check 6: Run actual CI checks
echo "Running CI checks locally..."
if uv run ruff format --check . > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ruff format check passes"
else
    echo -e "${YELLOW}⚠${NC}  Code needs formatting"
    echo "   Run: uv run ruff format ."
fi

if uv run ruff check . > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ruff lint check passes"
else
    echo -e "${YELLOW}⚠${NC}  Linting issues found"
    echo "   Run: uv run ruff check . --fix"
fi

echo ""
echo "======================================"

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Your CI/CD pipeline should work correctly."
    echo "Push your changes to trigger the CI:"
    echo "  git push"
else
    echo -e "${RED}❌ Found $ISSUES_FOUND issue(s) that need fixing${NC}"
    echo ""
    echo "Fix the issues above and run this script again."
fi
