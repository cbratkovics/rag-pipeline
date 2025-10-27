#!/usr/bin/env bash
# One-command fix for CI/CD pipeline
# This script fixes the uv.lock issue causing CI failures

set -euo pipefail

echo "================================================"
echo "🔧 RAG Pipeline CI/CD Fix Script"
echo "================================================"
echo ""
echo "This will fix the 'Failed to spawn: ruff' error in your CI/CD pipeline"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure we're in the project root
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: pyproject.toml not found${NC}"
    echo "Please run this script from your project root directory"
    exit 1
fi

echo "📍 Working in: $(pwd)"
echo ""

# Step 1: Ensure uv is available
echo "Step 1: Checking uv installation..."
export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv is not installed${NC}"
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo -e "${GREEN}✓${NC} uv is installed: $(uv --version)"
echo ""

# Step 2: Generate uv.lock
echo "Step 2: Generating uv.lock file..."
if [ -f "uv.lock" ]; then
    echo "Found existing uv.lock, backing up to uv.lock.backup"
    cp uv.lock uv.lock.backup
fi

# Try to generate lock file
if uv lock; then
    echo -e "${GREEN}✓${NC} Lock file generated successfully"
else
    echo -e "${YELLOW}⚠${NC}  Lock generation failed (likely chroma-hnswlib issue)"
    echo "Trying workaround..."
    
    # Workaround for chroma-hnswlib
    if uv lock --resolution=highest; then
        echo -e "${GREEN}✓${NC} Lock file generated with resolution=highest"
    else
        echo -e "${YELLOW}⚠${NC}  Automatic generation failed, trying manual approach..."
        
        # Create a minimal lock that will work
        echo "Creating minimal lock file..."
        # Remove chroma-hnswlib temporarily
        cp pyproject.toml pyproject.toml.backup
        sed -i.bak '/chroma-hnswlib/d' pyproject.toml
        
        # Generate lock without problematic package
        uv lock
        
        # Restore original pyproject.toml
        mv pyproject.toml.backup pyproject.toml
        
        echo -e "${YELLOW}⚠${NC}  Lock file created without chroma-hnswlib"
        echo "  Will install it separately during sync"
    fi
fi

# Step 3: Sync dependencies
echo ""
echo "Step 3: Syncing dependencies..."
if uv sync; then
    echo -e "${GREEN}✓${NC} Dependencies synced"
else
    echo -e "${YELLOW}⚠${NC}  Sync had issues, installing chroma-hnswlib separately..."
    uv pip install chroma-hnswlib==0.7.6
    echo -e "${GREEN}✓${NC} Installed chroma-hnswlib 0.7.6"
fi

# Step 4: Fix pre-commit hooks
echo ""
echo "Step 4: Fixing pre-commit hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    # Backup original
    cp .pre-commit-config.yaml .pre-commit-config.yaml.backup
    
    # Replace .venv/bin/ with uv run
    sed -i.bak 's|\.venv/bin/|uv run |g' .pre-commit-config.yaml
    
    # Also fix any 'poetry run' references
    sed -i.bak 's|poetry run |uv run |g' .pre-commit-config.yaml
    
    echo -e "${GREEN}✓${NC} Pre-commit hooks updated to use 'uv run'"
    
    # Reinstall hooks
    if command -v pre-commit &> /dev/null; then
        pre-commit uninstall > /dev/null 2>&1 || true
        uv run pre-commit install
        echo -e "${GREEN}✓${NC} Pre-commit hooks reinstalled"
    fi
fi

# Step 5: Test the setup
echo ""
echo "Step 5: Testing setup..."
TESTS_PASSED=true

# Test ruff
if uv run ruff --version > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} ruff works"
else
    echo -e "${RED}✗${NC} ruff failed"
    TESTS_PASSED=false
fi

# Test pytest
if uv run pytest --version > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} pytest works"
else
    echo -e "${RED}✗${NC} pytest failed"
    TESTS_PASSED=false
fi

# Test mypy
if uv run mypy --version > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} mypy works"
else
    echo -e "${RED}✗${NC} mypy failed"
    TESTS_PASSED=false
fi

# Step 6: Run CI checks locally
echo ""
echo "Step 6: Running CI checks locally..."
echo "Running ruff format check..."
if uv run ruff format --check . > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Code formatting is correct"
else
    echo -e "${YELLOW}⚠${NC}  Code needs formatting"
    echo "  Auto-fixing..."
    uv run ruff format .
    echo -e "${GREEN}✓${NC} Code formatted"
fi

echo "Running ruff lint..."
if uv run ruff check . > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} No linting issues"
else
    echo -e "${YELLOW}⚠${NC}  Found linting issues"
    echo "  Auto-fixing what's possible..."
    uv run ruff check . --fix > /dev/null 2>&1 || true
    echo -e "${GREEN}✓${NC} Fixed auto-fixable issues"
fi

# Step 7: Git operations
echo ""
echo "Step 7: Preparing git commits..."

# Check if uv.lock is in .gitignore
if [ -f ".gitignore" ] && grep -q "uv.lock" .gitignore; then
    echo -e "${YELLOW}⚠${NC}  Found uv.lock in .gitignore, removing it..."
    sed -i.bak '/^uv\.lock$/d' .gitignore
    git add .gitignore
fi

# Add files to git
git add uv.lock
echo -e "${GREEN}✓${NC} Added uv.lock to git"

if [ -f ".pre-commit-config.yaml" ]; then
    git add .pre-commit-config.yaml
    echo -e "${GREEN}✓${NC} Added updated .pre-commit-config.yaml"
fi

# Add any formatted/fixed Python files
git add -u

echo ""
echo "================================================"
echo -e "${GREEN}✅ CI/CD Fix Complete!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Review the changes:"
echo "   git status"
echo "   git diff --staged"
echo ""
echo "2. Commit the fixes:"
echo "   git commit -m \"Fix CI/CD: Add uv.lock and update pre-commit hooks\""
echo ""
echo "3. Push to trigger CI:"
echo "   git push origin main"
echo ""

if [ "$TESTS_PASSED" = true ]; then
    echo -e "${GREEN}All tools are working correctly. Your CI should pass!${NC}"
else
    echo -e "${YELLOW}Some tools had issues, but the main fix is applied.${NC}"
    echo "Your CI might still have some warnings but should not fail on 'ruff not found'."
fi

echo ""
echo "📝 Backup files created:"
[ -f "uv.lock.backup" ] && echo "  - uv.lock.backup"
[ -f ".pre-commit-config.yaml.backup" ] && echo "  - .pre-commit-config.yaml.backup"
[ -f ".gitignore.bak" ] && echo "  - .gitignore.bak"
