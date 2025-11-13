# Quick Start Guide - Production Fixes

## What Was Fixed

1. **Rate limiting on health endpoints** - Health checks will NEVER be rate-limited
2. **Empty vector store detection** - API logs clear warnings when vector store is empty
3. **Test scripts** - Automated verification of all fixes

## Immediate Deployment Steps

### 1. Deploy to Render (30 seconds)

```bash
# Commit and push
git add .
git commit -m "fix: rate limiting and vector store initialization"
git push
```

Render will auto-deploy.

### 2. Initialize Vector Store (1 minute)

After deployment completes, run:

```bash
curl -X POST https://rag-pipeline-api-hksb.onrender.com/api/v1/admin/initialize
```

Or use the helper script:

```bash
python scripts/init_deployed_store.py
```

### 3. Verify Deployment (30 seconds)

Test health endpoints (should never rate limit):

```bash
# Run 10 times - all should return 200
for i in {1..10}; do
  curl -s -o /dev/null -w "%{http_code} " https://rag-pipeline-api-hksb.onrender.com/healthz
done
echo
```

Expected output: `200 200 200 200 200 200 200 200 200 200`

### 4. Run Full Test Suite (2 minutes)

```bash
python scripts/test_deployment.py https://rag-pipeline-api-hksb.onrender.com
```

## Quick Verification Checklist

```bash
# 1. Health check (should return 200)
curl https://rag-pipeline-api-hksb.onrender.com/healthz

# 2. Vector store status (should show document count)
curl https://rag-pipeline-api-hksb.onrender.com/api/v1/admin/vector-store/status

# 3. Test query (should return non-zero scores)
curl -X POST https://rag-pipeline-api-hksb.onrender.com/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?"}'
```

## Expected Results

### Health Check Response
```json
{"status": "ok", "service": "rag-pipeline"}
```

### Vector Store Status (after initialization)
```json
{
  "status": "healthy",
  "document_count": 25,
  "search_working": true,
  "collection_name": "rag_documents",
  "persist_dir": "/opt/render/project/src/.chroma"
}
```

### Query Response
```json
{
  "answer": "Retrieval-Augmented Generation (RAG) is...",
  "sources": [
    {"score": 0.85, "document": {...}},
    {"score": 0.78, "document": {...}}
  ],
  "confidence_score": 0.82
}
```

**Key: All scores should be > 0!**

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Health check returns 429 | This was the bug we fixed! Redeploy. |
| Vector store empty | Run `POST /api/v1/admin/initialize` |
| All scores are zero | Reinitialize: `POST /api/v1/admin/initialize` with `{"reset": true}` |
| API won't start | Check Render logs for OPENAI_API_KEY error |

## Environment Variables to Check in Render

1. `OPENAI_API_KEY` - Must be set
2. `CORS_ORIGINS` - Must include frontend URL: `["https://rag-pipeline-eta.vercel.app"]`
3. `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` - Required for ChromaDB

## Success Indicators

✅ Render dashboard shows service as "healthy"
✅ Health check endpoint returns 200 (not 429 or 500)
✅ Vector store has 25+ documents
✅ Query returns non-zero scores
✅ No errors in Render logs
✅ Frontend can connect to API

## Total Time to Fix: ~5 minutes

1. Push code: 30 seconds
2. Wait for deploy: 2-3 minutes
3. Initialize vector store: 30 seconds
4. Verify: 1 minute

## Contact Points

- Health check: `https://rag-pipeline-api-hksb.onrender.com/healthz`
- Vector status: `https://rag-pipeline-api-hksb.onrender.com/api/v1/admin/vector-store/status`
- Initialize: `POST https://rag-pipeline-api-hksb.onrender.com/api/v1/admin/initialize`
- Query: `POST https://rag-pipeline-api-hksb.onrender.com/api/v1/query`
- Docs: `https://rag-pipeline-api-hksb.onrender.com/docs`

---

**You're ready to deploy!** The critical rate limiting bug is fixed. 🚀
