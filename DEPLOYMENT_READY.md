# Deployment Ready - Next Steps

## Changes Made

All configuration files have been updated and deployment files created. Your RAG pipeline is now ready for production deployment!

### Fixed Files
1. **`.pre-commit-config.yaml`** - Updated to use Poetry properly with explicit args
2. **`pyproject.toml`** - Modernized with `[project]` table to fix deprecation warnings
3. **`scripts/ci.sh`** - Verified (already properly configured)

### New Deployment Files
1. **`render.yaml`** - Render Blueprint for automated deployment
2. **`.env.render.example`** - Template for Render environment variables
3. **`docs/RENDER_DEPLOYMENT.md`** - Comprehensive deployment guide
4. **`docs/DEPLOYMENT_CHECKLIST.md`** - Step-by-step deployment checklist
5. **`README.md`** - Updated with production deployment section

## Required Actions Before Committing

### 1. Fix Script Permissions
```bash
chmod +x scripts/ci.sh
```

### 2. Reinstall Pre-commit Hooks
```bash
poetry run pre-commit install --install-hooks
```

### 3. Test Quality Checks Locally
```bash
make quality
```

If all checks pass, proceed to step 4.

### 4. Commit and Push (Manual - You Handle This)
```bash
git add .
git commit -m "fix: Update pre-commit hooks and add Render deployment config

- Fix .pre-commit-config.yaml to use Poetry with explicit args
- Modernize pyproject.toml with [project] table
- Add render.yaml for automated Render deployment
- Add comprehensive deployment documentation
- Update README with production deployment guide"

git push origin main
```

## Deployment Process

### Phase 1: Backend Deployment (Render)

1. **Go to Render Dashboard** (https://render.com)
2. **Create Redis Service:**
   - Click "New +" → "Redis"
   - Name: `rag-pipeline-redis`
   - Plan: Starter (Free tier available)
   - Region: Oregon
   - Click "Create"

3. **Deploy Backend:**
   - Click "New +" → "Blueprint"
   - Connect your GitHub repo
   - Select `render.yaml`
   - Click "Apply"

4. **Set Environment Variables:**
   - `OPENAI_API_KEY` - Your OpenAI key (if using OpenAI)
   - `CORS_ORIGINS` - Will update after Vercel deployment

5. **Wait for Deployment** (5-10 minutes)
6. **Copy Backend URL** (e.g., `https://rag-pipeline-api.onrender.com`)

### Phase 2: Frontend Deployment (Vercel)

1. **Go to Vercel Dashboard** (https://vercel.com)
2. **Import Repository:**
   - Click "Add New" → "Project"
   - Import your GitHub repo

3. **Configure Project:**
   - Root Directory: `frontend`
   - Framework Preset: Next.js
   - Build Command: (leave default)

4. **Set Environment Variables:**
   - `NEXT_PUBLIC_API_URL` - Your Render backend URL

5. **Deploy**
6. **Copy Frontend URL** (e.g., `https://your-app.vercel.app`)

### Phase 3: Final Configuration

1. **Update Backend CORS:**
   - Go to Render → Your Service → Environment
   - Update `CORS_ORIGINS` to `["https://your-app.vercel.app"]`
   - Click "Save Changes"

2. **Test End-to-End:**
   ```bash
   # Test backend health
   curl https://rag-pipeline-api.onrender.com/healthz

   # Test frontend
   # Visit https://your-app.vercel.app in browser
   ```

## Estimated Costs

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| Render Backend | Starter | $7 |
| Render Redis | Free | $0 |
| Vercel Frontend | Hobby | $0 |
| **Total** | | **$7/month** |

## Documentation Reference

- **Deployment Guide**: `docs/RENDER_DEPLOYMENT.md`
- **Checklist**: `docs/DEPLOYMENT_CHECKLIST.md`
- **Frontend Docs**: `frontend/README.md`
- **API Docs**: `http://localhost:8000/docs` (or your deployed URL)

## Troubleshooting

### Pre-commit Hooks Fail
```bash
# Ensure you ran chmod
chmod +x scripts/ci.sh

# Reinstall hooks
poetry run pre-commit uninstall
poetry run pre-commit install --install-hooks

# Test manually
poetry run pre-commit run --all-files
```

### Quality Checks Fail
```bash
# Auto-fix formatting
poetry run ruff format .

# Auto-fix linting
poetry run ruff check . --fix

# Run tests
poetry run pytest tests/ -m "not integration"
```

### Render Deployment Fails
- Check build logs in Render dashboard
- Verify all environment variables are set
- Ensure `poetry.lock` is committed
- Check that `render.yaml` is in repo root

### Vercel Deployment Fails
- Verify root directory is set to `frontend`
- Check that `NEXT_PUBLIC_API_URL` is set
- Review build logs for dependency issues

## Next Steps After Deployment

1. Initialize vector store with seed data (see `docs/RENDER_DEPLOYMENT.md` Step 4)
2. Test query flow end-to-end
3. Monitor logs and metrics
4. Set up alerts (optional)
5. Configure custom domain (optional)

## Success Checklist

- [ ] Scripts have execute permissions (`chmod +x scripts/ci.sh`)
- [ ] Pre-commit hooks reinstalled
- [ ] Local quality checks pass (`make quality`)
- [ ] Changes committed and pushed to GitHub
- [ ] Render Redis deployed
- [ ] Render backend deployed
- [ ] Vercel frontend deployed
- [ ] CORS configured with frontend URL
- [ ] End-to-end test successful
- [ ] Monitoring dashboards accessible

## Questions?

Refer to:
- `docs/RENDER_DEPLOYMENT.md` for backend deployment details
- `docs/DEPLOYMENT_CHECKLIST.md` for step-by-step checklist
- `frontend/README.md` for frontend-specific documentation

---

**You're ready to deploy!** Follow the steps above and you'll have a production RAG pipeline running in under 30 minutes.
