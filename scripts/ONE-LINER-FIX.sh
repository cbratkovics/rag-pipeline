#!/bin/bash
# ONE-LINER FIX - Copy and paste this single command to fix CI

echo "Copy and run this ENTIRE command block:"
echo "========================================"
cat << 'EOF'
uv run ruff format . && \
find . -name "*.py" -type f -exec sed -i 's/\r$//' {} \; && \
find src api -name "*.py" -type f -exec sed -i 's/[[:space:]]*# type: ignore.*//g' {} \; && \
uv run ruff format . && \
git add -A && \
git commit -m "fix(ci): apply ruff formatting and remove unused type ignores" && \
git push && \
echo "✅ DONE! Check your GitHub Actions - it should pass now!"
EOF

echo ""
echo "========================================"
echo "Or run step by step:"
echo "========================================"
echo "1. Format code:           uv run ruff format ."
echo "2. Fix line endings:      find . -name '*.py' -type f -exec sed -i 's/\r$//' {} \\;"
echo "3. Remove type ignores:   find src api -name '*.py' -type f -exec sed -i 's/[[:space:]]*# type: ignore.*//g' {} \\;"
echo "4. Format again:          uv run ruff format ."
echo "5. Stage changes:         git add -A"
echo "6. Commit:               git commit -m 'fix(ci): apply ruff formatting'"
echo "7. Push:                 git push"
echo ""
echo "========================================"
