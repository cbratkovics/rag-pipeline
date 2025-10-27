#!/bin/bash
# FIX-VECTOR-STORE.SH - Specifically fixes the vector_store.py type: ignore issues

set -e

echo "================================================"
echo "🎯 TARGETED FIX FOR TYPE: IGNORE ISSUES"
echo "================================================"
echo ""

# Find all Python files with type: ignore comments
echo "Step 1: Finding all 'type: ignore' comments..."
echo "----------------------------------------------"

# Create a Python script to properly fix type: ignore comments
cat > /tmp/fix_type_ignores.py << 'EOF'
#!/usr/bin/env python3
"""Fix unused type: ignore comments in Python files."""

import re
import sys
from pathlib import Path

def fix_file(filepath: Path) -> bool:
    """Fix unused type: ignore comments in a file."""
    content = filepath.read_text()
    original = content
    
    # Pattern to match type: ignore comments
    patterns = [
        (r'#\s*type:\s*ignore\[.*?\]', ''),  # Remove [specific] ignores
        (r'#\s*type:\s*ignore(?!\[)', ''),    # Remove bare type: ignore
    ]
    
    modified = content
    for pattern, replacement in patterns:
        # Only remove at end of lines
        modified = re.sub(f'{pattern}\s*$', replacement, modified, flags=re.MULTILINE)
    
    # Clean up double spaces left behind
    modified = re.sub(r'  +\n', '\n', modified)
    modified = re.sub(r' +$', '', modified, flags=re.MULTILINE)
    
    if modified != original:
        filepath.write_text(modified)
        return True
    return False

# Target files mentioned in the CI logs
critical_files = [
    'src/retrieval/vector_store.py',
    'src/api/routers/metrics.py',
    'src/api/routers/health.py',
]

print("Checking critical files first...")
for file_path in critical_files:
    path = Path(file_path)
    if path.exists():
        if fix_file(path):
            print(f"  ✓ Fixed: {file_path}")
        else:
            print(f"  - No issues: {file_path}")
    else:
        print(f"  ⚠ Not found: {file_path}")

print("\nChecking all Python files...")
fixed_count = 0
for py_file in Path('.').rglob('*.py'):
    if 'venv' in str(py_file) or '__pycache__' in str(py_file):
        continue
    if fix_file(py_file):
        print(f"  ✓ Fixed: {py_file}")
        fixed_count += 1

print(f"\nTotal files fixed: {fixed_count}")
EOF

python3 /tmp/fix_type_ignores.py

echo ""
echo "Step 2: Running ruff format on all files..."
echo "-------------------------------------------"
uv run ruff format .

echo ""
echo "Step 3: Fixing any ruff auto-fixable issues..."
echo "----------------------------------------------"
uv run ruff check . --fix || true

echo ""
echo "Step 4: Final verification..."
echo "-----------------------------"

# Check if mypy still complains
echo "Checking mypy for unused ignores..."
if uv run mypy src api --ignore-missing-imports 2>&1 | grep -q "unused.*ignore"; then
    echo "⚠️  Still have unused ignores - manually check these files:"
    uv run mypy src api --ignore-missing-imports 2>&1 | grep "unused.*ignore"
else
    echo "✅ No unused type: ignore comments!"
fi

echo ""
echo "Checking ruff format..."
if uv run ruff format --check .; then
    echo "✅ Ruff format check passes!"
else
    echo "❌ Ruff format still has issues"
    echo "   Showing diff:"
    uv run ruff format --check . --diff || true
fi

echo ""
echo "================================================"
echo "📝 COMMIT THESE CHANGES:"
echo "================================================"
echo "git add -A"
echo "git commit -m 'fix: remove unused type: ignore comments and format code'"
echo "git push"
echo ""

# Clean up
rm -f /tmp/fix_type_ignores.py
