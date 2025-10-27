#!/usr/bin/env bash
# Script to generate uv.lock with chroma-hnswlib workaround
set -euo pipefail

echo "================================================"
echo "Generating uv.lock with chroma-hnswlib workaround"
echo "================================================"
echo ""

# Ensure uv is in PATH
export PATH="$HOME/.local/bin:$PATH"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed or not in PATH"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✓ Using uv version: $(uv --version)"
echo ""

# Clean existing lock file
if [ -f "uv.lock" ]; then
    echo "Removing existing uv.lock..."
    rm -f uv.lock
fi

# Step 1: Generate lock file
echo "Step 1: Generating uv.lock..."
if uv lock; then
    echo "✓ Lock file generated successfully!"
else
    echo "⚠️  Initial lock generation failed (expected due to chroma-hnswlib)"
    echo "Trying alternative approach..."
    
    # Try with highest resolution strategy
    if uv lock --resolution=highest; then
        echo "✓ Lock file generated with highest resolution"
    else
        echo "❌ Could not generate lock file automatically"
        echo ""
        echo "Manual workaround required:"
        echo "1. Temporarily comment out 'chroma-hnswlib' in pyproject.toml"
        echo "2. Run: uv lock"
        echo "3. Uncomment 'chroma-hnswlib'"
        echo "4. Run: uv sync"
        echo "5. Manually edit uv.lock to use chroma-hnswlib==0.7.6"
        exit 1
    fi
fi

# Step 2: Sync dependencies
echo ""
echo "Step 2: Syncing dependencies..."
if uv sync; then
    echo "✓ Dependencies synced successfully!"
else
    echo "⚠️  Sync failed, attempting to install chroma-hnswlib separately..."
    uv pip install chroma-hnswlib==0.7.6
    echo "✓ Installed chroma-hnswlib 0.7.6 (with binary wheels)"
fi

# Step 3: Verify installation
echo ""
echo "Step 3: Verifying installation..."
echo "Testing imports..."

if uv run python -c "import chromadb; print('✓ ChromaDB imports successfully')"; then
    :
else
    echo "❌ ChromaDB import failed"
fi

if uv run python -c "import ruff; print('✓ Ruff imports successfully')"; then
    :
else
    echo "❌ Ruff import failed"
fi

# Step 4: Test tools
echo ""
echo "Step 4: Testing development tools..."

if uv run ruff --version > /dev/null 2>&1; then
    echo "✓ Ruff: $(uv run ruff --version)"
else
    echo "❌ Ruff not working"
fi

if uv run pytest --version > /dev/null 2>&1; then
    echo "✓ Pytest: $(uv run pytest --version | head -1)"
else
    echo "❌ Pytest not working"
fi

if uv run mypy --version > /dev/null 2>&1; then
    echo "✓ Mypy: $(uv run mypy --version)"
else
    echo "❌ Mypy not working"
fi

# Step 5: Run basic CI checks
echo ""
echo "Step 5: Running basic CI checks..."

echo "Running ruff format check..."
if uv run ruff format --check . > /dev/null 2>&1; then
    echo "✓ Code formatting is correct"
else
    echo "⚠️  Code needs formatting (run: uv run ruff format .)"
fi

echo "Running ruff linting..."
if uv run ruff check . > /dev/null 2>&1; then
    echo "✓ No linting issues"
else
    echo "⚠️  Linting issues found (run: uv run ruff check .)"
fi

echo ""
echo "================================================"
echo "✅ Setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Commit the uv.lock file:"
echo "   git add uv.lock"
echo "   git commit -m 'Add uv.lock for CI/CD pipeline'"
echo ""
echo "2. Update .pre-commit-config.yaml with the fixed version"
echo "   git add .pre-commit-config.yaml"
echo "   git commit -m 'Fix pre-commit hooks to use uv run'"
echo ""
echo "3. Push to trigger CI:"
echo "   git push"
echo ""
echo "If you still see issues in CI, check that:"
echo "- uv.lock is committed and not in .gitignore"
echo "- The .github/workflows/ci.yml uses 'uv sync --frozen'"
