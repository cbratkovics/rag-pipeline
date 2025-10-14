#!/usr/bin/env bash

echo "🔧 Fixing RAG Pipeline Configuration..."
echo ""

# Step 1: Make CI script executable
echo "1. Making CI script executable..."
chmod +x scripts/ci.sh
echo "✓ Done"
echo ""

# Step 2: Regenerate Poetry lock file
echo "2. Regenerating Poetry lock file..."
if poetry lock --no-update; then
    echo "✓ Lock file regenerated successfully"
else
    echo "❌ Failed to regenerate lock file"
    echo "Run manually: poetry lock --no-update"
    exit 1
fi
echo ""

# Step 3: Reinstall pre-commit hooks
echo "3. Reinstalling pre-commit hooks..."
if poetry run pre-commit uninstall && poetry run pre-commit install; then
    echo "✓ Hooks reinstalled successfully"
else
    echo "❌ Failed to reinstall hooks"
    exit 1
fi
echo ""

# Step 4: Test hooks
echo "4. Testing pre-commit hooks..."
if poetry run pre-commit run --all-files; then
    echo "✓ All hooks passed!"
else
    echo "⚠️  Some hooks failed - check output above"
    echo "This is normal if you have uncommitted changes"
fi
echo ""

echo "✅ Setup complete!"
echo ""
echo "You can now commit your changes:"
echo "  git add ."
echo "  git commit -m \"fix: Update pre-commit hooks and Poetry config\""
echo "  git push origin main"
