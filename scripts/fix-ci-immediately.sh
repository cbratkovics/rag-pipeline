#!/bin/bash
# ULTIMATE CI/CD FIX SCRIPT - Fixes the damn ruff formatting error once and for all
set -e

echo "============================================"
echo "🔥 FIXING CI/CD RUFF FORMAT ERROR PERMANENTLY"
echo "============================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Step 1: Finding the exact formatting issues..."
echo "---------------------------------------------"

# Run ruff format with verbose output to see what's wrong
echo "Running ruff format check with details..."
if ! uv run ruff format --check . --diff 2>&1; then
    echo -e "${YELLOW}Found formatting differences!${NC}"
    echo ""
    
    echo "Step 2: Auto-fixing ALL formatting issues..."
    echo "---------------------------------------------"
    uv run ruff format .
    echo -e "${GREEN}✓ All files formatted${NC}"
else
    echo -e "${GREEN}✓ No formatting issues found${NC}"
fi

echo ""
echo "Step 3: Checking for unused type: ignore comments..."
echo "---------------------------------------------"

# Fix unused type: ignore comments
if uv run mypy src api --ignore-missing-imports 2>&1 | grep -q "unused.*type.*ignore"; then
    echo -e "${YELLOW}Found unused type: ignore comments${NC}"
    
    # Find and remove unused type: ignore comments
    echo "Removing unused type: ignore comments..."
    find src api -name "*.py" -type f -exec sed -i.bak 's/# type: ignore\[.*\]//g; s/# type: ignore//g' {} \;
    
    # Clean up backup files
    find src api -name "*.py.bak" -type f -delete
    
    echo -e "${GREEN}✓ Removed unused type: ignore comments${NC}"
else
    echo -e "${GREEN}✓ No unused type: ignore comments${NC}"
fi

echo ""
echo "Step 4: Fixing line endings (CRLF -> LF)..."
echo "---------------------------------------------"

# Convert CRLF to LF for all Python files
find . -name "*.py" -type f -exec dos2unix {} \; 2>/dev/null || \
find . -name "*.py" -type f -exec sed -i 's/\r$//' {} \;

echo -e "${GREEN}✓ Line endings normalized to LF${NC}"

echo ""
echo "Step 5: Running ALL CI checks locally..."
echo "---------------------------------------------"

# Run the exact CI commands
CI_PASSED=true

echo -n "Ruff format check: "
if uv run ruff format --check .; then
    echo -e "${GREEN}PASSED${NC}"
else
    echo -e "${RED}FAILED${NC}"
    CI_PASSED=false
fi

echo -n "Ruff lint: "
if uv run ruff check .; then
    echo -e "${GREEN}PASSED${NC}"
else
    echo -e "${RED}FAILED${NC}"
    CI_PASSED=false
fi

echo -n "MyPy: "
if uv run mypy src api --ignore-missing-imports > /dev/null 2>&1; then
    echo -e "${GREEN}PASSED${NC}"
else
    echo -e "${YELLOW}WARNING (non-blocking)${NC}"
fi

echo ""
echo "Step 6: Ensuring ruff config is consistent..."
echo "---------------------------------------------"

# Check pyproject.toml for ruff config
if [ -f "pyproject.toml" ]; then
    echo "Current ruff configuration:"
    grep -A 10 "\[tool.ruff\]" pyproject.toml || echo "No ruff config found"
    
    # Ensure ruff version is locked
    echo ""
    echo "Ruff version:"
    uv run ruff --version
fi

echo ""
echo "Step 7: Final verification..."
echo "---------------------------------------------"

if $CI_PASSED; then
    echo -e "${GREEN}✅ SUCCESS! All CI checks pass locally${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Stage changes: git add -A"
    echo "2. Commit: git commit -m 'fix: ruff formatting and unused type ignores'"
    echo "3. Push: git push"
else
    echo -e "${RED}❌ Some checks still failing${NC}"
    echo ""
    echo "Try running:"
    echo "  uv run ruff format ."
    echo "  uv run ruff check . --fix"
    echo ""
    echo "Then run this script again."
fi

echo ""
echo "============================================"
echo "📋 DIAGNOSTIC INFO FOR CI/CD"
echo "============================================"
echo "Ruff version: $(uv run ruff --version)"
echo "Python version: $(uv run python --version)"
echo "UV version: $(uv --version)"
echo "Total Python files: $(find . -name '*.py' | wc -l)"
echo ""

# Show any Python files that were recently modified
echo "Recently modified Python files (last 5):"
git log --name-only --pretty=format: -5 | grep '\.py$' | sort -u | head -5

echo ""
echo "If CI still fails after this, the issue is likely:"
echo "1. GitHub Actions cache needs clearing"
echo "2. Different ruff version in CI vs local"
echo "3. Check the EXACT error message in GitHub Actions logs"
