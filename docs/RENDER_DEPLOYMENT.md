# Render Deployment Guide

## Prerequisites

1. Render account (sign up at https://render.com)
2. GitHub repository connected to Render
3. OpenAI API key (if using OpenAI provider)

## Step 1: Deploy Redis Cache

1. Go to Render Dashboard
2. Click "New +" → "Redis"
3. Configure:
   - **Name**: `rag-pipeline-redis`
   - **Region**: Oregon (or closest to you)
   - **Plan**: Starter (Free tier available)
   - **Max Memory Policy**: `allkeys-lru`
4. Click "Create Redis"
5. Wait for deployment (2-3 minutes)
6. Copy the **Internal Redis URL** (starts with `redis://`)

## Step 2: Deploy FastAPI Backend

### Option A: Using render.yaml (Recommended)

1. Push `render.yaml` to your GitHub repo
2. In Render Dashboard: "New +" → "Blueprint"
3. Select your repository
4. Render will auto-detect `render.yaml`
5. Click "Apply"
6. Set environment variables:
   - `OPENAI_API_KEY` - Your OpenAI key
   - `CORS_ORIGINS` - Update with your Vercel URL after frontend deployment
7. Click "Deploy"

### Option B: Manual Setup

1. In Render Dashboard: "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `rag-pipeline-api`
   - **Region**: Oregon
   - **Branch**: main
   - **Root Directory**: `.` (blank)
   - **Runtime**: Python 3
   - **Build Command**:
     ```bash
     pip install poetry && poetry install --only main
     ```
   - **Start Command**:
     ```bash
     poetry run uvicorn api.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Starter ($7/month)

4. Add Environment Variables:
   - Copy from `.env.render.example`
   - Set `REDIS_URL` to the Redis Internal URL from Step 1
   - Set `OPENAI_API_KEY` to your OpenAI key
   - Set `CORS_ORIGINS` to `["https://your-app.vercel.app"]` (update after Vercel deployment)

5. Set Health Check:
   - **Path**: `/healthz`

6. Click "Create Web Service"

## Step 3: Post-Deployment

1. Wait for deployment (5-10 minutes)
2. Copy your backend URL: `https://rag-pipeline-api.onrender.com`
3. Test health endpoint:
   ```bash
   curl https://rag-pipeline-api.onrender.com/healthz
   ```
4. Should return: `{"status": "ok"}`

## Step 4: Initialize Vector Store

SSH into your Render service or use the Shell:

```bash
# In Render Shell
poetry run python -m src.rag.ingest --data-dir data/seed --reset
```

Or trigger via API:
```bash
curl -X POST https://rag-pipeline-api.onrender.com/api/v1/ingest
```

## Step 5: Update Vercel Frontend

1. Go to Vercel project settings
2. Add environment variable:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://rag-pipeline-api.onrender.com`
3. Redeploy frontend

## Monitoring

- **Logs**: Render Dashboard → Your Service → Logs
- **Metrics**: Render Dashboard → Your Service → Metrics
- **Health**: `https://rag-pipeline-api.onrender.com/healthz`
- **API Docs**: `https://rag-pipeline-api.onrender.com/docs`
- **Prometheus Metrics**: `https://rag-pipeline-api.onrender.com/metrics`

## Troubleshooting

### Service Won't Start
- Check logs in Render Dashboard
- Verify all environment variables are set
- Ensure Poetry dependencies install correctly
- Check that `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` is set

### Connection Errors
- Verify Redis URL is correct
- Check CORS_ORIGINS includes your Vercel domain
- Ensure health check path is `/healthz`

### Performance Issues
- Upgrade to Standard plan ($25/month)
- Enable autoscaling in Render settings
- Add caching headers to API responses
- Monitor with Prometheus metrics

### ChromaDB Errors
- Ensure `CHROMA_PERSIST_DIR` is set to `/opt/render/project/.chroma`
- Verify protobuf environment variable is set
- Check that vector store is initialized with seed data

### OpenAI API Errors
- Verify `OPENAI_API_KEY` is set correctly
- Check API key has sufficient credits
- System will fall back to StubLLM if OpenAI fails

## Environment Variables Reference

### Required
- `CORS_ORIGINS` - Array of allowed frontend URLs
- `REDIS_URL` - Redis connection string (auto-set by Render)

### Optional
- `OPENAI_API_KEY` - OpenAI API key (only if using OpenAI provider)
- `LLM_PROVIDER` - "stub" or "openai" (default: "stub")
- `EMBEDDING_MODEL` - Sentence transformer model (default: "all-MiniLM-L6-v2")
- `HYBRID_WEIGHT_BM25` - BM25 weight for fusion (default: 0.5)
- `HYBRID_WEIGHT_VECTOR` - Vector weight for fusion (default: 0.5)

## Costs

| Service | Plan | Cost |
|---------|------|------|
| FastAPI Backend | Starter | $7/month |
| Redis Cache | Free/Starter | $0-5/month |
| **Total** | | **$7-12/month** |

Free tier available for hobby projects with some limitations.

## Updating the Deployment

### Auto-Deploy (Default)
- Push to main branch on GitHub
- Render automatically builds and deploys

### Manual Deploy
1. Go to Render Dashboard
2. Select your service
3. Click "Manual Deploy" → "Deploy latest commit"

### Rolling Back
1. Go to Render Dashboard
2. Select your service
3. Click "Events" tab
4. Find previous successful deployment
5. Click "Rollback to this version"

## Security Best Practices

1. **Restrict CORS Origins**: Update `CORS_ORIGINS` to only include your production frontend URL
2. **Secure Redis**: Add IP whitelist in Redis settings for production
3. **Environment Variables**: Never commit `.env` files - use Render's environment variable management
4. **API Keys**: Rotate OpenAI API keys regularly
5. **HTTPS**: Render provides SSL certificates automatically
6. **Rate Limiting**: Consider adding rate limiting to API endpoints

## Next Steps

After successful deployment:

1. Test the API with your frontend
2. Monitor logs and metrics
3. Set up alerts in Render dashboard
4. Configure custom domain (optional)
5. Enable autoscaling for production traffic
6. Set up backup strategy for ChromaDB data
