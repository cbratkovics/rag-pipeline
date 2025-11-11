# Migration Guide: Frontend Fixes, Python 3.12, and uv Transition

## Overview

This document outlines the changes made to modernize the RAG pipeline project, including fixing critical Vercel frontend issues, upgrading Python to 3.12, and preparing for migration to `uv` dependency management.

---

## 🎯 What Was Fixed

### ✅ Frontend (Complete)
1. **Fixed Vercel Build Failure** - Corrupted `favicon.ico` blocking builds
2. **Patched Security Vulnerability** - Next.js 14.2.5 → 14.2.33 (1 critical CVE)
3. **Added Missing Utility Functions** - `formatDuration`, `formatCost`, `formatNumber`
4. **Verified TypeScript Compilation** - Zero errors
5. **Verified ESLint** - Zero warnings

### ✅ Backend (Python 3.12 Upgrade Complete)
1. **Updated Python Version** - 3.11 → 3.12 across all configs
2. **Created `.python-version`** - Ensures environment consistency
3. **Updated Dockerfile** - Python 3.12-slim base images
4. **Updated CI/CD** - GitHub Actions, Render config
5. **Generated `requirements.txt`** - Via uv for future migration

### ⚠️ Backend (uv Migration - Needs Manual Completion)
- `uv` installed and functional (v0.9.2)
- `requirements.txt` generated successfully (175 packages resolved)
- **Blocker**: `chroma-hnswlib==0.7.3` fails to compile on macOS ARM64 with Python 3.12
  - Issue: Package uses `-march=native` flag incompatible with Apple Silicon
  - **Resolution**: Install dependencies on Linux (Docker/CI) OR use Poetry temporarily

---

## 📁 Modified Files

### Frontend
```
frontend/app/favicon.ico           DELETED (was corrupt HTML comment)
frontend/app/icon.tsx               CREATED (dynamic icon generation)
frontend/package.json               Next.js 14.2.5 → 14.2.33
frontend/lib/api.ts                 Added formatDuration, formatCost, formatNumber
```

### Backend
```
.python-version                     CREATED (content: "3.12")
pyproject.toml                      python = "^3.12", target-version = "py312"
Dockerfile                          python:3.12-slim (both stages)
render.yaml                         PYTHON_VERSION: 3.12.0
.github/workflows/ci.yml            PYTHON_VERSION: "3.12"
requirements.txt                    CREATED (175 packages, ready for uv)
```

---

## 🚀 Deployment Instructions

### Frontend Deployment (Vercel)

**Status**: ✅ Ready to deploy

The frontend build is now passing locally. Vercel should build successfully with these fixes.

#### Vercel Environment Variables (Required)
```bash
NEXT_PUBLIC_API_URL=https://rag-pipeline-api-hksb.onrender.com
NODE_VERSION=20
```

#### Build Settings (Already Configured in `vercel.json`)
- **Framework**: Next.js
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Install Command**: `npm install`

### Backend Deployment (Python 3.12)

**Status**: ✅ Ready for Linux environments | ⚠️ macOS needs workaround

#### Option A: Deploy Directly (Recommended for Production)
Deploy to Docker/Render/GitHub Actions - these Linux environments will build successfully.

```bash
# Docker build (should work)
docker build -t rag-pipeline:latest .

# Render deploy (auto-deploys from GitHub with updated render.yaml)
git push origin main
```

#### Option B: Local macOS Development (Poetry Workaround)
Until `chroma-hnswlib` is fixed for Python 3.12 on ARM, use Poetry locally:

```bash
# Temporarily use Poetry for local dev
poetry env use 3.11  # Downgrade temporarily for local dev
poetry install

# OR: Use Docker for local testing
docker-compose up --build
```

---

## 🔄 uv Migration Commands (When Ready)

### Current State
- `uv` installed: `/Users/christopherbratkovics/.local/bin/uv`
- `requirements.txt` generated and ready
- Dependencies resolved: 175 packages

### Migration Steps (Post chroma-hnswlib Fix)

#### 1. Install Dependencies
```bash
# Sync all dependencies
uv sync

# Or install from requirements.txt
uv pip install -r requirements.txt
```

#### 2. Run Tests
```bash
# Unit tests
uv run pytest tests/ -m "not integration"

# With coverage
uv run pytest tests/ --cov=src --cov=api
```

#### 3. Run Linting/Formatting
```bash
uv run ruff check .
uv run ruff format .
uv run mypy src api
```

#### 4. Run Application
```bash
# Start API server
uv run uvicorn src.api.main:app --reload

# Run ingestion
uv run python -m src.rag.ingest

# Run evaluation
uv run python -m src.eval.ragas_runner
```

#### 5. Add New Dependencies
```bash
# Add production dependency
uv add <package>

# Add development dependency
uv add --dev <package>
```

---

## 📝 Scripts That Will Need Updating (Future)

When `uv` migration is complete, update these files:

### `scripts/ci.sh`
```bash
# OLD
.venv/bin/pytest tests/

# NEW
uv run pytest tests/
```

### `.pre-commit-config.yaml`
```yaml
# Update tool paths if needed
entry: uv run ruff
```

### `Makefile`
```makefile
# OLD
poetry run pytest

# NEW
uv run pytest
```

### `Dockerfile`
```dockerfile
# Replace Poetry with uv
RUN pip install --no-cache-dir uv
RUN uv pip install --no-cache -r requirements.txt
```

---

## 🐛 Known Issues & Workarounds

### Issue 1: chroma-hnswlib Build Failure (macOS ARM64 + Python 3.12)

**Error**:
```
clang++: error: unsupported argument 'native' to option '-march='
```

**Workarounds**:
1. **Use Python 3.11 locally** (temporary)
   ```bash
   pyenv install 3.11.8
   pyenv local 3.11.8
   poetry install
   ```

2. **Use Docker for development**
   ```bash
   docker-compose up --build
   make dev-run  # If Makefile supports Docker
   ```

3. **Wait for upstream fix** - Track https://github.com/nmslib/hnswlib/issues

### Issue 2: Poetry Lock File Out of Sync

**Error**:
```
Warning: poetry.lock is not consistent with pyproject.toml
```

**Solution**:
```bash
poetry lock --no-update
```

---

## ✅ Verification Checklist

### Frontend
- [x] `npm install` - No vulnerabilities
- [x] `npm run build` - Successful
- [x] `npm run lint` - No errors
- [x] `npm run type-check` - Passes

### Backend (On Linux/CI)
- [ ] `docker build` - Should succeed with Python 3.12
- [ ] `pytest tests/` - All tests pass
- [ ] API starts: `uvicorn src.api.main:app`

### Backend (On macOS - Workaround)
- [ ] Use Poetry with Python 3.11 OR
- [ ] Use Docker for local development

---

## 📊 Dependency Comparison

### Old Stack
```
Python: 3.11
Package Manager: Poetry
Next.js: 14.2.5 (vulnerable)
Total Python Packages: ~175
```

### New Stack
```
Python: 3.12 ✅
Package Manager: uv (pending full migration)
Next.js: 14.2.33 (secure) ✅
Total Python Packages: 175 (resolved)
```

---

## 🎓 Key Learnings

1. **Favicon Format Matters**: Next.js strictly validates image formats - HTML comments break builds
2. **Security Patching**: Always use `npm audit` before deploying frontends
3. **Python 3.12 Compatibility**: Some C extensions (like chroma-hnswlib) lag behind new Python releases
4. **uv Benefits**: 10-100x faster than pip/poetry for dependency resolution
5. **Cross-Platform Testing**: Test builds on target deployment OS (Linux for production)

---

## 🚦 Next Steps for You

### Immediate (Frontend)
1. ✅ Review modified files (listed above)
2. ✅ Test frontend locally: `cd frontend && npm run dev`
3. Push to trigger Vercel deployment

### Short-term (Backend)
1. Test backend build in Docker: `docker build -t rag-pipeline .`
2. If Docker build succeeds, push to main branch
3. Monitor Render deployment

### Long-term (uv Migration)
1. Wait for `chroma-hnswlib` Python 3.12 support OR
2. Consider alternative vector DB (e.g., `qdrant-client` already in deps)
3. Complete uv migration when builds succeed
4. Update all scripts/CI to use `uv run`

---

## 📞 Support & Resources

- **uv Documentation**: https://github.com/astral-sh/uv
- **Next.js 14 Metadata**: https://nextjs.org/docs/app/api-reference/file-conventions/metadata
- **chroma-hnswlib Issue**: https://github.com/chroma-core/hnswlib/issues
- **Poetry to uv Guide**: https://docs.astral.sh/uv/guides/integration/poetry/

---

**Generated**: 2025-10-14
**Python Version Target**: 3.12
**Frontend Status**: ✅ Production-ready
**Backend Status**: ⚠️ Requires Linux environment for full build
