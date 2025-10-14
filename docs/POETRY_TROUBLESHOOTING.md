# Poetry Troubleshooting Guide

## Issue: Permission Denied Error with Poetry Virtual Environment

### Symptoms

When running `poetry lock --no-update` or other Poetry commands, you encounter:
```
[Errno 13] Permission denied: 'python'
```

### Root Cause

This issue occurs when:
1. Poetry's virtual environment has corrupted symlinks
2. Poetry (installed under a different Python version) has compatibility issues with the project's Python version
3. macOS quarantine attributes block execution

### Solution Applied (October 14, 2025)

#### 1. Identified the Problem

The `.venv` directory had broken symlinks:
```bash
.venv/bin/python -> python3.11
.venv/bin/python3.11 -> /usr/local/opt/python@3.11/bin/python3.11
```

Poetry (version 2.1.4) was installed under Python 3.12 but the project required Python 3.11, causing internal conflicts.

#### 2. Fixed the Virtual Environment

**Step 1: Remove corrupted environment**
```bash
rm -rf .venv
```

**Step 2: Create fresh virtual environment using Python's venv module**
```bash
/usr/local/bin/python3.11 -m venv .venv
```

This bypassed Poetry's broken virtual environment creation.

**Step 3: Install dependencies using pip**
```bash
# Upgrade pip
.venv/bin/python -m pip install --upgrade pip

# Install Poetry in the virtual environment
.venv/bin/python -m pip install poetry

# Install all dependencies from requirements.txt
.venv/bin/python -m pip install -r requirements.txt

# Install dev dependencies
.venv/bin/python -m pip install pytest==7.4.4 pytest-cov==4.1.0 pytest-asyncio==0.21.2 \
    pytest-mock==3.12.0 pytest-env==1.1.3 responses ruff mypy bandit locust \
    types-requests ipython pre-commit faker
```

#### 3. Updated Configuration Files

**`.pre-commit-config.yaml`**: Changed from `poetry run` to direct `.venv/bin/` paths:
```yaml
- id: ruff-format
  entry: .venv/bin/ruff format  # Changed from: poetry run ruff format
```

**`scripts/ci.sh`**: Updated all commands to use `.venv/bin/` directly:
```bash
.venv/bin/ruff format --check .  # Changed from: poetry run ruff format --check .
```

#### 4. Reinstalled Pre-commit Hooks

```bash
.venv/bin/pre-commit uninstall
.venv/bin/pre-commit install
```

### Verification

All tools now work correctly:
```bash
$ .venv/bin/python --version
Python 3.11.13

$ .venv/bin/pip check
No broken requirements found.

$ .venv/bin/ruff --version
ruff 0.14.0

$ .venv/bin/mypy --version
mypy 1.18.2

$ .venv/bin/pytest --co -q
collected 37 items
```

## How to Prevent This in the Future

1. **Use consistent Python versions**: Ensure Poetry is installed under the same Python version as your project requires
2. **Use virtual environments in-project**: Set `virtualenvs.in-project = true` in Poetry config
3. **Regular maintenance**: Periodically rebuild virtual environments if they become stale
4. **Alternative approach**: Consider using `pip` and `requirements.txt` for simpler dependency management

## Quick Reference for Common Issues

### "Poetry command not found"
```bash
# Use the venv-installed version
.venv/bin/poetry <command>
```

### "Cannot find module X"
```bash
# Reinstall dependencies
.venv/bin/python -m pip install -r requirements.txt
```

### "Pre-commit hook failed"
```bash
# Verify hook uses .venv/bin/ paths
cat .pre-commit-config.yaml | grep entry
```

### "Tests not found"
```bash
# Run tests directly with full path
.venv/bin/pytest tests/ -v
```

## Migration Notes

**Before**: System relied on Poetry for all command execution
```bash
poetry run ruff format .
poetry run pytest tests/
```

**After**: Direct virtual environment usage
```bash
.venv/bin/ruff format .
.venv/bin/pytest tests/
```

This approach provides:
- Faster execution (no Poetry overhead)
- More reliable (bypasses Poetry's virtual environment issues)
- Simpler debugging (direct paths are easier to understand)

## Related Files Modified

- `.pre-commit-config.yaml` - Updated all hook entries
- `scripts/ci.sh` - Updated all command paths
- `.venv/` - Completely rebuilt from scratch
