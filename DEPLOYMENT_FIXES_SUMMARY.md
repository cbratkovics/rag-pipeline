# Deployment Fixes Summary

## Critical Issues Fixed

### 1. Rate Limiting Middleware Fix ✅
**File:** `src/api/middleware.py` (lines 41-52)

**Problem:** Health check endpoints were being rate-limited, causing 429/500 errors on Render.

**Solution:** Added health endpoint exclusion at the beginning of `rate_limit_middleware()`:
```python
# CRITICAL: Skip rate limiting for health check endpoints
health_paths = [
    "/healthz",
    "/health",
    "/api/v1/health",
    "/api/v1/health/ready",
    "/api/v1/health/live",
    "/metrics",
]
if request.url.path in health_paths:
    response: Response = await call_next(request)
    return response
```

**Impact:** Health checks will NEVER be rate-limited, fixing the Render deployment issue.

---

### 2. Vector Store Auto-Check ✅
**File:** `src/api/main.py` (lines 46-57)

**Problem:** API started successfully even with empty vector store, causing silent failures.

**Solution:** Added vector store count check in lifespan function:
```python
# Check vector store and warn if empty
try:
    count = await vector_store.count_documents()
    if count == 0:
        logger.warning(
            "⚠️  Vector store is EMPTY! The API will start but queries will fail. "
            "Please initialize with: POST /api/v1/admin/initialize"
        )
    else:
        logger.info(f"✓ Vector store contains {count} documents")
except Exception as e:
    logger.error(f"Failed to check vector store status: {e}")
```

**Impact:** Clear warnings in logs when vector store needs initialization.

---

### 3. Comprehensive Test Scripts ✅

#### Test Deployment Script
**File:** `scripts/test_deployment.py`

**Purpose:** Comprehensive deployment verification for production.

**Features:**
- Tests health endpoints (no rate limiting)
- Verifies vector store has documents
- Tests query endpoint with non-zero scores
- Validates CORS headers
- Tests rate limiting on query endpoints
- Checks Prometheus metrics

**Usage:**
```bash
# Test local deployment
python scripts/test_deployment.py http://localhost:8000

# Test production deployment
python scripts/test_deployment.py https://your-app.onrender.com
```

#### Local Test Script
**File:** `scripts/test_local.py`

**Purpose:** Local development testing and verification.

**Features:**
- Checks if API is running
- Auto-initializes vector store if empty
- Tests health and query endpoints
- Runs diagnostics
- Provides next steps

**Usage:**
```bash
# Start API first, then run:
python scripts/test_local.py
```

---

### 4. Environment Configuration Template ✅
**File:** `.env.render`

**Purpose:** Template for Render environment variables.

**Key Variables:**
- `OPENAI_API_KEY` - Required for production
- `CORS_ORIGINS` - Frontend URLs (JSON array)
- `RATE_LIMIT_ENABLED=true`
- `CHROMA_PERSIST_DIR=/opt/render/project/src/.chroma`
- `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` - Critical for ChromaDB

---

## Existing Components (Already Working)

### Admin Router ✅
**File:** `src/api/routers/admin.py`

**Endpoints:**
- `POST /api/v1/admin/initialize` - Initialize vector store with seed docs
- `GET /api/v1/admin/vector-store/status` - Get document count and health
- `POST /api/v1/admin/vector-store/verify` - Run verification tests

### Initialization Script ✅
**File:** `scripts/initialize_vector_store.py`

**Features:**
- 25 comprehensive seed documents about RAG, vector search, embeddings, etc.
- Supports both local and Render paths
- Can load additional files from `data/seed/`
- Includes verification function

---

## Testing Procedure

### Local Testing

1. **Start the API:**
   ```bash
   # Make sure .env has OPENAI_API_KEY set
   $HOME/.local/bin/uv run uvicorn src.api.main:app --reload --port 8000
   ```

2. **Verify health endpoints work:**
   ```bash
   # These should NEVER return 429
   curl http://localhost:8000/healthz
   curl http://localhost:8000/api/v1/health
   curl http://localhost:8000/api/v1/health/ready
   ```

3. **Check vector store status:**
   ```bash
   curl http://localhost:8000/api/v1/admin/vector-store/status
   ```

4. **Initialize if empty:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/initialize
   ```

5. **Test query endpoint:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"query": "What is RAG?"}'
   ```

6. **Run comprehensive tests:**
   ```bash
   python scripts/test_deployment.py http://localhost:8000
   ```

### Production Testing (Render)

1. **Deploy to Render:**
   - Push code to GitHub
   - Render auto-deploys

2. **Set environment variables in Render Dashboard:**
   - Copy from `.env.render`
   - Ensure `OPENAI_API_KEY` is set
   - Set `CORS_ORIGINS` to include frontend URL

3. **Check deployment logs:**
   - Look for "Vector store is EMPTY" warning
   - Verify "All components initialized successfully"

4. **Initialize vector store:**
   ```bash
   curl -X POST https://your-app.onrender.com/api/v1/admin/initialize
   ```

5. **Verify health endpoints:**
   ```bash
   # Make 10 requests quickly - none should be rate limited
   for i in {1..10}; do
     curl -s -o /dev/null -w "%{http_code} " https://your-app.onrender.com/healthz
   done
   echo
   ```

6. **Run deployment tests:**
   ```bash
   python scripts/test_deployment.py https://your-app.onrender.com
   ```

---

## Success Criteria

- [ ] Health endpoints return 200, never 429 or 500
- [ ] Vector store contains at least 25 documents
- [ ] Query endpoint returns answers with non-zero scores
- [ ] CORS headers include frontend URL
- [ ] Rate limiting works on query endpoints (not health)
- [ ] All tests in `test_deployment.py` pass
- [ ] API starts with clear warning if vector store is empty

---

## Deployment Checklist

### Before Deploying to Render

1. [ ] Verify rate limiting fix in `src/api/middleware.py`
2. [ ] Verify auto-check in `src/api/main.py`
3. [ ] Test scripts are executable: `chmod +x scripts/*.py`
4. [ ] `.env.render` has all required variables
5. [ ] Local tests pass

### After Deploying to Render

1. [ ] Check deployment logs for errors
2. [ ] Verify health check is working (Render dashboard shows "healthy")
3. [ ] Initialize vector store via admin endpoint
4. [ ] Verify vector store has documents
5. [ ] Test query endpoint returns non-zero scores
6. [ ] Run `test_deployment.py` against production URL
7. [ ] Test frontend can connect to API

---

## Troubleshooting

### Issue: Health checks return 500
**Solution:** This was the main issue we fixed. Deploy the updated `middleware.py`.

### Issue: Vector store is empty
**Solution:** Call `POST /api/v1/admin/initialize` or run `scripts/initialize_vector_store.py`.

### Issue: All query scores are zero
**Solution:** Vector store needs reinitialization. Call admin endpoint with `reset=true`.

### Issue: CORS errors from frontend
**Solution:** Update `CORS_ORIGINS` in Render environment variables to include frontend URL.

### Issue: Rate limiting too aggressive
**Solution:** Adjust `RATE_LIMIT_REQUESTS_PER_MINUTE` in environment variables.

---

## Files Modified

1. `src/api/middleware.py` - Added health endpoint exclusion
2. `src/api/main.py` - Added vector store count check
3. `scripts/test_deployment.py` - NEW comprehensive test script
4. `scripts/test_local.py` - NEW local test runner
5. `.env.render` - NEW environment template

## Files Already Existing (Used by fixes)

1. `src/api/routers/admin.py` - Admin endpoints
2. `scripts/initialize_vector_store.py` - Vector store initialization
3. `scripts/init_deployed_store.py` - Production initialization helper

---

## Next Steps

1. **Commit and push changes:**
   ```bash
   git add .
   git commit -m "fix: rate limiting on health endpoints and vector store initialization"
   git push
   ```

2. **Deploy to Render** (automatic via GitHub integration)

3. **Initialize production vector store:**
   ```bash
   python scripts/init_deployed_store.py
   # Or manually:
   curl -X POST https://your-app.onrender.com/api/v1/admin/initialize
   ```

4. **Verify deployment:**
   ```bash
   python scripts/test_deployment.py https://your-app.onrender.com
   ```

5. **Test frontend integration** by opening your Vercel app

---

## Summary

All critical issues have been fixed:
- ✅ Rate limiting no longer affects health endpoints
- ✅ Vector store status is checked on startup
- ✅ Comprehensive test scripts created
- ✅ Environment configuration documented
- ✅ Clear error messages for empty vector store

The deployment should now be stable on Render with proper health checks.
