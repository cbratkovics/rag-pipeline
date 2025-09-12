#!/usr/bin/env bash
set -euo pipefail

echo "Installing pre-commit hooks..."

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install the git hooks
pre-commit install --install-hooks
pre-commit install --hook-type pre-push

echo "✓ Pre-commit hooks installed successfully!"
echo "✓ Code will be automatically checked before commits"
echo "✓ Full CI suite will run before pushes"