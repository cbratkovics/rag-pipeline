# Frontend Setup Guide

Quick guide to get the RAG Pipeline frontend running locally and deployed to production.

## Prerequisites

- Node.js 18+ and npm
- Backend API running (see main README)
- Git for version control

## Local Development

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_ANALYTICS=false
```

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 4. Test Backend Connection

The app will show a connection error if the backend isn't running. Make sure:
1. Backend is running at `http://localhost:8000`
2. You can access `http://localhost:8000/healthz`
3. CORS is configured (see below)

## Backend CORS Configuration

Update `api/main.py` to allow frontend requests:

```python
cors_origins = os.getenv("CORS_ORIGINS", json.dumps([
    "http://localhost:3000",           # Local development
    "https://your-app.vercel.app",     # Production
    "https://*.vercel.app"              # Preview deployments
]))
```

Restart the backend after changing CORS settings.

## Production Deployment

### Option 1: Vercel (Recommended)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

4. **Set Environment Variables**
   In Vercel dashboard:
   - `NEXT_PUBLIC_API_URL` = Your backend URL (e.g., https://your-backend.onrender.com)
   - `NEXT_PUBLIC_ENABLE_ANALYTICS` = true

### Option 2: Manual Build

```bash
cd frontend
npm run build
npm start
```

The app will be available at `http://localhost:3000`

## Common Issues

### "Failed to fetch" Error

**Cause**: Backend not accessible or CORS not configured

**Solution**:
1. Check backend is running: `curl http://localhost:8000/healthz`
2. Verify `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check browser console for CORS errors
4. Update CORS settings in `api/main.py`

### Build Errors

**Cause**: Missing dependencies or TypeScript errors

**Solution**:
```bash
rm -rf node_modules .next
npm install
npm run build
```

### Styling Not Working

**Cause**: Tailwind not configured correctly

**Solution**:
1. Verify `globals.css` is imported in `app/layout.tsx`
2. Check `tailwind.config.ts` content paths
3. Restart dev server

## File Structure Overview

```
frontend/
├── app/                    # Next.js App Router
│   ├── page.tsx           # Main page
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── ui/               # Shadcn components
│   ├── QueryInterface.tsx
│   ├── ResultsDisplay.tsx
│   ├── MetricsPanel.tsx
│   ├── RAGASScores.tsx
│   └── SourceCitations.tsx
├── lib/                   # Utilities
│   ├── api.ts            # API client
│   └── utils.ts          # Helpers
├── types/                 # TypeScript types
│   └── index.ts
├── package.json
└── .env.local            # Your config (create this)
```

## Development Tips

### Hot Reload

Changes to any file will automatically reload the page.

### TypeScript Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

### Testing API Endpoints

Use the browser DevTools Network tab to inspect API calls:
1. Open DevTools (F12)
2. Go to Network tab
3. Submit a query
4. Check the `/api/v1/query` request

## Next Steps

1. Test the query interface with sample questions
2. Explore advanced settings (retrieval parameters)
3. Try different A/B test variants
4. Check RAGAS evaluation scores
5. Deploy to Vercel for public access

## Support

- **Frontend Issues**: [frontend/README.md](frontend/README.md)
- **Backend Issues**: [README.md](README.md)
- **GitHub Issues**: https://github.com/cbratkovics/rag-pipeline/issues

---

Happy building! 🚀
