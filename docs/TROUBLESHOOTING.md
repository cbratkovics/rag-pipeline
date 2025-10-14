# Troubleshooting Guide

## Pre-commit Hook Errors

### Error: `[Errno 13] Permission denied: 'python'`

**Cause:** Pre-commit hooks trying to use system Python instead of Poetry virtual environment.

**Solution:**
```bash
# 1. Make sure you're in Poetry virtual environment
poetry shell

# 2. Run the fix script
chmod +x scripts/fix-hooks.sh
bash scripts/fix-hooks.sh

# 3. Or manually:
chmod +x scripts/ci.sh
poetry lock --no-update
poetry run pre-commit uninstall
poetry run pre-commit install
```

### Error: `pyproject.toml changed significantly since poetry.lock was last generated`

**Cause:** Changes to pyproject.toml are incompatible with existing lock file.

**Solution:**
```bash
# Regenerate lock file without updating dependencies
poetry lock --no-update

# Or update all dependencies (may change versions)
poetry lock

# If that fails, try:
rm poetry.lock
poetry install
```

### Hooks Still Failing After Fix

**Debug steps:**
```bash
# 1. Verify Poetry environment
poetry env info

# 2. Check which Python is being used
poetry run which python

# 3. Manually test each hook
poetry run ruff format .
poetry run ruff check .
poetry run mypy src api --ignore-missing-imports
poetry run pytest -m unit

# 4. Run hooks manually
poetry run pre-commit run --all-files
```

## Git Commit Blocked

### Skip hooks temporarily (NOT RECOMMENDED for main branch)
```bash
git commit --no-verify -m "your message"
```

### Fix properly
```bash
# Run fix script
chmod +x scripts/fix-hooks.sh
bash scripts/fix-hooks.sh

# Or step by step:
poetry run ruff format .
poetry run ruff check . --fix
git add .
git commit -m "fix: Format and lint code"
```

## Poetry Lock File Issues

### Lock file corrupted
```bash
rm poetry.lock
poetry install
```

### Dependency conflicts
```bash
# Check for conflicts
poetry check

# Update specific dependency
poetry update package-name

# Update all dependencies
poetry update
```

## Permission Issues on macOS

### Scripts not executable
```bash
# Make all scripts executable
chmod +x scripts/*.sh

# Or specific script
chmod +x scripts/ci.sh
```

### Python permission denied
```bash
# Ensure you're in Poetry virtual environment
poetry shell

# Check Python location
which python  # Should be in .venv or Poetry cache

# If using system Python, recreate venv
poetry env remove python
poetry install
```

## Quick Fixes

### Reset everything
```bash
# Nuclear option - start fresh
rm -rf .venv poetry.lock
poetry install
poetry run pre-commit install
```

### Bypass all checks (emergency only)
```bash
# Commit without running hooks
SKIP=all git commit -m "emergency commit"

# Or disable specific hook
SKIP=pytest-fast git commit -m "skip tests"
```

## Common Issues

### "poetry: command not found"
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="$HOME/.local/bin:$PATH"
```

### "Python version not found"
```bash
# Check available Python versions
poetry env info

# Use specific Python version
poetry env use 3.11

# Or use system Python
poetry env use $(which python3.11)
```

### "Module not found" errors in tests
```bash
# Reinstall dependencies
poetry install --sync

# Clear cache and reinstall
poetry cache clear . --all
poetry install
```

## Getting Help

If issues persist:
1. Check Poetry version: `poetry --version` (should be 1.7.0+)
2. Check Python version: `python --version` (should be 3.11+)
3. Check pre-commit version: `poetry run pre-commit --version`
4. Review logs in `.git/hooks/` directory
5. Open issue on GitHub with full error output

## Useful Commands

```bash
# Check Poetry configuration
poetry config --list

# Verify virtual environment
poetry env info

# Show installed packages
poetry show

# Update specific package
poetry update package-name

# Run command in Poetry environment
poetry run <command>

# Activate virtual environment
poetry shell
```
