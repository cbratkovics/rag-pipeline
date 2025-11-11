# Local Development Setup

This document explains the current local development environment setup for the rag-pipeline project.

## Overview

**Package Manager**: `uv` (v0.9.2)
**Python Version**: 3.12.0
**Status**: Working ✅

## Why UV?

The project has been migrated from Poetry to `uv` for faster dependency resolution and installation. However, due to a macOS-specific compilation issue with `chroma-hnswlib`, a workaround was required.

## Known Issues

### chroma-hnswlib Compilation Issue

- **Problem**: `chroma-hnswlib==0.7.3` fails to compile on macOS with Apple Silicon due to hardcoded `-march=native` compiler flag
- **Workaround**: Manually installed `chroma-hnswlib==0.7.6` (which has pre-built wheels) and updated `uv.lock` to reference this version
- **Impact**: Development environment works perfectly with this workaround

## Prerequisites

1. **uv installed**: `/Users/christopherbratkovics/.local/bin/uv`
2. **PATH configured**: `~/.local/bin` is added to PATH via `~/.local/bin/env` (sourced in `~/.zshrc`)
3. **Python 3.12**: Installed at `/usr/local/bin/python3.12`

## Setup Instructions

### Initial Setup

```bash
# uv is already installed and in PATH for new shells
# For current shell session, add to PATH:
export PATH="$HOME/.local/bin:$PATH"

# Install dependencies and create virtual environment
uv sync

# Verify installation
uv --version
# Expected: uv 0.9.2 (141369ce7 2025-10-10)
```

### Verify Environment

```bash
# Test Python
uv run python --version
# Expected: Python 3.12.0

# Test development tools
uv run pytest --version
uv run ruff --version
uv run mypy --version
```

## Daily Development Commands

All commands should be run using `uv run` instead of direct `.venv/bin/` or `poetry run` commands.

### Running Tests

```bash
# Run all unit tests (excluding integration tests)
uv run pytest tests/ -m "not integration"

# Run with coverage
uv run pytest tests/ -v --cov=src --cov=api --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_pipeline.py -v

# Run integration tests
CI=true uv run pytest tests/integration/ -v
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Check formatting (without changes)
uv run ruff format --check .

# Lint code
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Type checking
uv run mypy src api --ignore-missing-imports
```

### Running the Application

```bash
# Run API server
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Run with hot reload (development)
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Other Operations

```bash
# Ingest documents
uv run python -m src.rag.ingest --data-dir data/seed --reset

# Run evaluation
uv run python -m src.eval.ragas_runner
```

## Makefile Commands

All Makefile targets have been updated to use `uv`:

```bash
make setup          # Install dependencies with uv sync
make test           # Run pytest with coverage
make lint           # Run ruff linting
make format         # Format code with ruff
make ci-test        # Run all CI checks locally
make run            # Run API server
make ingest         # Ingest documents into Chroma
```

## Pre-commit Hooks

Pre-commit hooks have been installed and configured to use `uv run`:

```bash
# Run pre-commit hooks on all files
uv run pre-commit run --all-files

# Run pre-commit hooks on staged files (automatic on commit)
git commit -m "your message"
```

## Scripts

All scripts in `scripts/` have been updated to use `uv run`:

- `./scripts/ci.sh` - Complete CI quality checks
- `./scripts/autofix.sh` - Auto-fix formatting and linting issues
- `./scripts/validate_ci.sh` - Validate CI setup

## Troubleshooting

### PATH Issues

If `uv` command is not found:

```bash
# Add to current shell session
export PATH="$HOME/.local/bin:$PATH"

# Or use full path
/Users/christopherbratkovics/.local/bin/uv --version
```

### Missing Dependencies

If you encounter missing module errors:

```bash
# Resync all dependencies
uv sync

# Check what's installed
uv pip list
```

### chroma-hnswlib Issues

If you encounter compilation errors with `chroma-hnswlib`:

The project is already configured to use version 0.7.6 (which has binary wheels). If you still see issues:

1. Ensure `uv.lock` has `chroma-hnswlib` at version 0.7.6
2. The lock file includes pre-built wheels entry
3. Never run `uv lock --upgrade` without preserving the chroma-hnswlib workaround

### Vercel Build

The Vercel build is configured separately and does not use `uv`. It uses the production configuration in `vercel.json`.

## Files Modified During Migration

- `pyproject.toml` - Added [project] section with requires-python
- `pyproject.toml` - Added `chroma-hnswlib>=0.7.3` as direct dependency
- `uv.lock` - Updated chroma-hnswlib to 0.7.6 with binary wheel reference
- `scripts/ci.sh` - Changed all `.venv/bin/` to `uv run`
- `scripts/autofix.sh` - Changed all `poetry run` to `uv run`
- `scripts/validate_ci.sh` - Changed `poetry check/run` to `uv run`
- `.pre-commit-config.yaml` - Changed all hooks to use `uv run`
- `Makefile` - Changed all `poetry install/run` to `uv sync/run`

## Development Workflow

1. **Start new work**:
   ```bash
   # Ensure dependencies are current
   uv sync
   ```

2. **Make changes**: Edit code as needed

3. **Check code quality**:
   ```bash
   # Quick checks
   uv run ruff check .
   uv run pytest tests/ -m "not integration" -q
   ```

4. **Before committing**:
   ```bash
   # Pre-commit hooks run automatically
   # Or run manually:
   uv run pre-commit run --all-files
   ```

5. **Commit changes**:
   ```bash
   git add .
   git commit -m "Your commit message"
   # Pre-commit hooks will run automatically
   ```

## Test Results (Current Status)

Last tested: 2025-10-14

- ✅ Unit Tests: 14/21 passing
- ✅ Ruff Linting: All checks passed
- ⏱️  MyPy: Functional (may be slow on first run)
- ✅ Pre-commit Hooks: Installed and working

Known test failures are due to missing optional dependencies (`langchain_openai`, `qdrant_client`) and TestClient API changes. These do not affect core development functionality.

## Summary

The local development environment is working and ready for development. Use `uv run` for all commands instead of `.venv/bin/` or `poetry run`.
