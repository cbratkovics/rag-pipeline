# Deployment Checklist

## Pre-Deployment

- [ ] All tests passing locally (`make quality`)
- [ ] Environment variables documented in `.env.render.example`
- [ ] Dependencies locked (`poetry.lock` up to date)
- [ ] README updated with deployment instructions
- [ ] API documentation generated (FastAPI `/docs` endpoint)
- [ ] Security audit completed (no exposed secrets)
- [ ] `.gitignore` includes `.env` and sensitive files
- [ ] Pre-commit hooks configured and working
- [ ] CI/CD pipeline runs successfully

## Render Backend Deployment

### Redis Cache
- [ ] Redis service created on Render
- [ ] Region selected (Oregon recommended)
- [ ] Plan selected (Free/Starter)
- [ ] Max memory policy set to `allkeys-lru`
- [ ] Internal Redis URL copied

### Web Service
- [ ] Repository connected to Render
- [ ] Blueprint imported (`render.yaml`) OR manual setup completed
- [ ] Build command verified: `pip install poetry && poetry install --only main`
- [ ] Start command verified: `poetry run uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- [ ] Health check path set to `/healthz`
- [ ] Auto-deploy enabled on main branch

### Environment Variables
- [ ] `CORS_ORIGINS` - Set to frontend URL
- [ ] `REDIS_URL` - Auto-configured from Redis service
- [ ] `OPENAI_API_KEY` - **REQUIRED** Set manually in Render dashboard
- [ ] `OPENAI_MODEL` - Set to "gpt-3.5-turbo" (or custom model)
- [ ] `EMBEDDING_MODEL` - Set to model name
- [ ] `CHROMA_PERSIST_DIR` - Set to `/opt/render/project/.chroma`
- [ ] `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION` - Set to `python`
- [ ] `HYBRID_WEIGHT_BM25` - Set to 0.5 (or custom value)
- [ ] `HYBRID_WEIGHT_VECTOR` - Set to 0.5 (or custom value)

### Post-Deployment
- [ ] Service deployed successfully (check Render dashboard)
- [ ] Health check passing (`/healthz` returns 200)
- [ ] Vector store initialized with seed data
- [ ] Test API endpoint works (`/api/v1/query`)
- [ ] Logs show no critical errors
- [ ] Metrics endpoint accessible (`/metrics`)

## Vercel Frontend Deployment

### Pre-Deployment
- [ ] Frontend code in `frontend/` directory
- [ ] `package.json` and dependencies updated
- [ ] Environment variables documented

### Vercel Setup
- [ ] Repository imported to Vercel
- [ ] Root directory set to `frontend`
- [ ] Framework preset set to Next.js
- [ ] Build command verified (default: `next build`)
- [ ] Output directory verified (default: `.next`)

### Environment Variables
- [ ] `NEXT_PUBLIC_API_URL` - Set to Render backend URL
- [ ] Other frontend env vars set as needed

### Post-Deployment
- [ ] Build successful
- [ ] Preview deployment tested
- [ ] Production deployment live
- [ ] Frontend connects to backend successfully
- [ ] No CORS errors in browser console

## End-to-End Testing

### Functionality
- [ ] Test query submission from frontend
- [ ] Verify response includes answer and contexts
- [ ] Test A/B variant switching (if implemented)
- [ ] Test source citations display
- [ ] Test error handling (invalid queries, network errors)
- [ ] Test loading states and UI feedback

### Performance
- [ ] Query latency < 2 seconds (target: < 1.5s P99)
- [ ] No memory leaks observed
- [ ] ChromaDB responses fast (< 500ms)
- [ ] Redis cache working (check hit/miss rates)
- [ ] Prometheus metrics collecting properly

### Cross-Browser Testing
- [ ] Test on Chrome
- [ ] Test on Firefox
- [ ] Test on Safari
- [ ] Test on mobile devices

### Security
- [ ] HTTPS enabled (automatic on Render/Vercel)
- [ ] CORS configured correctly (no wildcard in production)
- [ ] No sensitive data in client-side code
- [ ] API keys secured in environment variables
- [ ] Rate limiting considered (if needed)

## Monitoring & Observability

- [ ] Render logs accessible and monitored
- [ ] Prometheus metrics endpoint working
- [ ] Error tracking configured (optional: Sentry)
- [ ] Uptime monitoring configured (optional: UptimeRobot)
- [ ] Alert notifications set up for critical failures

## Documentation

- [ ] Deployment guide completed (`docs/RENDER_DEPLOYMENT.md`)
- [ ] README includes deployment section
- [ ] API documentation accessible at `/docs`
- [ ] Environment variables documented
- [ ] Troubleshooting guide available

## Optional Enhancements

- [ ] Custom domain configured
- [ ] CDN configured for static assets
- [ ] Database backup strategy implemented
- [ ] Autoscaling enabled for production traffic
- [ ] Staging environment created
- [ ] CI/CD pipeline triggers automated deployments

## Post-Launch

- [ ] Announce deployment to team/users
- [ ] Monitor logs for first 24 hours
- [ ] Collect user feedback
- [ ] Review performance metrics
- [ ] Plan for future iterations

## Rollback Plan

In case of critical issues:
- [ ] Know how to rollback on Render (Events → Rollback)
- [ ] Know how to rollback on Vercel (Deployments → Redeploy previous)
- [ ] Have backup of environment variables
- [ ] Have backup of ChromaDB data (if applicable)
- [ ] Document rollback procedure for team

## Success Criteria

All items checked = Ready for production launch!

**Deployment Date**: _______________
**Deployed By**: _______________
**Backend URL**: _______________
**Frontend URL**: _______________
