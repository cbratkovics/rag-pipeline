#!/bin/bash
# DIAGNOSE-CI.SH - Find the EXACT issue causing CI to fail

echo "============================================"
echo "🔍 CI/CD DIAGNOSTIC TOOL"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Running diagnostics...${NC}"
echo ""

# 1. Check ruff format with verbose output
echo "1. RUFF FORMAT CHECK (this is failing in CI)"
echo "---------------------------------------------"
echo "Running: uv run ruff format --check ."
echo ""

if ! uv run ruff format --check . 2>&1; then
    echo -e "${RED}❌ RUFF FORMAT CHECK FAILED!${NC}"
    echo ""
    echo "This is your problem! Showing files that need formatting:"
    echo "---------------------------------------------------------"
    uv run ruff format --check . --diff 2>&1 | head -50
    echo ""
    echo -e "${YELLOW}FIX: Run 'uv run ruff format .' to auto-fix${NC}"
else
    echo -e "${GREEN}✅ Ruff format check passed${NC}"
fi

echo ""
echo "2. CHECK FOR COMMON ISSUES"
echo "---------------------------"

# Check for CRLF line endings
echo -n "Checking for CRLF line endings: "
if grep -rIl $'\r$' --include="*.py" . 2>/dev/null | head -1 | grep -q .; then
    echo -e "${RED}FOUND!${NC}"
    echo "  Files with Windows line endings:"
    grep -rIl $'\r$' --include="*.py" . 2>/dev/null | head -5
    echo -e "  ${YELLOW}FIX: Run 'find . -name \"*.py\" -exec sed -i 's/\r$//' {} \\;'${NC}"
else
    echo -e "${GREEN}OK (using LF)${NC}"
fi

# Check for tabs
echo -n "Checking for tabs in Python files: "
if grep -P '\t' --include="*.py" -r . 2>/dev/null | head -1 | grep -q .; then
    echo -e "${RED}FOUND!${NC}"
    echo "  Files with tabs:"
    grep -l -P '\t' --include="*.py" -r . 2>/dev/null | head -5
else
    echo -e "${GREEN}OK (no tabs)${NC}"
fi

# Check for trailing whitespace
echo -n "Checking for trailing whitespace: "
if grep -r '[[:space:]]$' --include="*.py" . 2>/dev/null | head -1 | grep -q .; then
    echo -e "${YELLOW}FOUND (minor)${NC}"
    COUNT=$(grep -r '[[:space:]]$' --include="*.py" . 2>/dev/null | wc -l)
    echo "  $COUNT lines with trailing whitespace"
else
    echo -e "${GREEN}OK${NC}"
fi

echo ""
echo "3. VERSION INFORMATION"
echo "----------------------"
echo "Python: $(uv run python --version)"
echo "Ruff: $(uv run ruff --version)"
echo "UV: $(uv --version)"

echo ""
echo "4. GITHUB ACTIONS CI COMMAND"
echo "-----------------------------"
echo "Your CI runs this exact command:"
echo -e "${BLUE}uv run ruff format --check .${NC}"
echo ""
echo "Test it locally:"
echo "$ uv run ruff format --check ."
echo ""

echo ""
echo "5. QUICK FIX COMMANDS"
echo "---------------------"
echo -e "${GREEN}Run these commands in order:${NC}"
echo ""
echo "# 1. Format all Python files"
echo "uv run ruff format ."
echo ""
echo "# 2. Fix line endings (if needed)"
echo "find . -name '*.py' -type f -exec sed -i 's/\r$//' {} \\;"
echo ""
echo "# 3. Stage all changes"
echo "git add -A"
echo ""
echo "# 4. Commit with a clear message"
echo "git commit -m 'fix: apply ruff formatting to all files'"
echo ""
echo "# 5. Push to trigger CI"
echo "git push"
echo ""

# Final check
echo "============================================"
if uv run ruff format --check . > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Your code is ready for CI!${NC}"
else
    echo -e "${RED}❌ Your code needs formatting!${NC}"
    echo ""
    echo -e "${YELLOW}Run this NOW:${NC}"
    echo -e "${BLUE}uv run ruff format . && git add -A && git commit -m 'fix: ruff formatting' && git push${NC}"
fi
echo "============================================"
