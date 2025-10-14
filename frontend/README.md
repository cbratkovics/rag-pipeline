# RAG Pipeline Frontend

Modern, production-ready Next.js frontend for the RAG Pipeline, showcasing enterprise AI engineering capabilities with real-time metrics, A/B testing, and RAGAS evaluation.

## Features

- **Interactive Query Interface**: Clean search experience with advanced parameter controls
- **Real-Time Metrics**: Latency, token count, cost estimation, and performance tracking
- **RAGAS Evaluation**: Visual display of context relevancy, answer faithfulness, and quality metrics
- **Source Citations**: Collapsible accordion showing retrieved documents with relevance scores
- **A/B Testing**: Variant selection for experimentation (Auto, Baseline, Reranked, Hybrid)
- **Hybrid Retrieval Visualization**: See how BM25 and vector search combine via RRF
- **Responsive Design**: Mobile-first, works seamlessly on all devices
- **Production-Ready**: Error handling, retry logic, loading states, and analytics

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: TailwindCSS
- **Components**: Shadcn/ui (Radix UI primitives)
- **State Management**: React Query (@tanstack/react-query)
- **Icons**: Lucide React
- **Analytics**: Vercel Analytics
- **Deployment**: Vercel

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Backend running at `http://localhost:8000` (or configured API URL)

### Installation

```bash
cd frontend
npm install
```

### Environment Setup

Create `.env.local` file:

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_ANALYTICS=true
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
npm run build
npm start
```

### Type Checking

```bash
npm run type-check
```

## Project Structure

```
frontend/
├── app/                      # Next.js App Router
│   ├── page.tsx             # Main application page
│   ├── layout.tsx           # Root layout with providers
│   ├── globals.css          # Global styles and Tailwind
│   └── favicon.ico          # App icon
├── components/              # React components
│   ├── ui/                  # Shadcn/ui base components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── badge.tsx
│   │   ├── accordion.tsx
│   │   ├── progress.tsx
│   │   └── tooltip.tsx
│   ├── QueryInterface.tsx   # Search bar & settings
│   ├── ResultsDisplay.tsx   # Answer with typing animation
│   ├── MetricsPanel.tsx     # Performance metrics
│   ├── RAGASScores.tsx      # Evaluation metrics
│   ├── SourceCitations.tsx  # Document sources
│   └── QueryProvider.tsx    # React Query provider
├── lib/                     # Utilities
│   ├── api.ts              # Backend API client
│   └── utils.ts            # Helper functions
├── types/                   # TypeScript definitions
│   └── index.ts            # API types matching backend
├── public/                  # Static assets
│   └── favicon.ico
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── .env.example
```

## API Integration

The frontend communicates with the FastAPI backend via REST endpoints:

### Query Endpoint

**POST** `/api/v1/query`

Request:
```typescript
{
  question: string;
  k?: number;              // Final results (default: 4)
  top_k_bm25?: number;     // BM25 results (default: 8)
  top_k_vec?: number;      // Vector results (default: 8)
  rrf_k?: number;          // RRF parameter (default: 60)
  provider?: 'stub' | 'openai';  // LLM provider
}
```

Response:
```typescript
{
  answer: string;
  contexts: string[];
  scores: Record<string, number>;
  latency_ms: number;
  metadata?: SourceMetadata[];
  timing?: {
    retrieval_ms: number;
    generation_ms: number;
    total_ms: number;
  };
}
```

### Health Check

**GET** `/healthz`

Response:
```typescript
{
  status: string;
}
```

## Key Components

### QueryInterface

Search bar with collapsible advanced settings:
- Retrieval parameters (k, top_k_bm25, top_k_vec, rrf_k)
- LLM provider selection (stub vs OpenAI)
- A/B test variant selection
- Keyboard shortcuts (Cmd/Ctrl + Enter)

### ResultsDisplay

Answer display with:
- Typing animation effect
- Confidence score badge
- Timing breakdown (retrieval, generation, total)
- Visual score indicators

### MetricsPanel

Four key metrics cards:
- Latency (ms/s)
- Contexts retrieved
- Token count (estimated)
- Cost (USD, for OpenAI)

### RAGASScores

Evaluation metrics with progress bars:
- Context Relevancy
- Answer Faithfulness
- Answer Relevancy
- Context Recall
- Overall RAGAS score

Each metric shows:
- Current value vs target threshold
- Visual progress bar
- Quality label (Good/Fair/Poor)
- Tooltips with explanations

### SourceCitations

Collapsible accordion for each source:
- Document title and ID
- Relevance score
- Retrieval method badge (BM25/Vector/Hybrid)
- Full content display
- Copy-to-clipboard functionality
- Character count

## Development Guidelines

### Code Style

- Use TypeScript strict mode
- Follow ESLint + Next.js config
- Prefer functional components with hooks
- Use Tailwind utility classes over custom CSS
- Implement error boundaries for production

### Performance

- Lazy load heavy components
- Memoize expensive calculations with `useMemo`
- Debounce user input (300ms)
- Use React Query for request deduplication
- Optimize images with Next.js Image component

### Error Handling

- All API calls wrapped in try-catch
- Display user-friendly error messages
- Retry logic with exponential backoff
- Graceful degradation if backend unavailable
- Network error detection

## Deployment

### Vercel (Recommended)

1. **Connect Repository**
   ```bash
   vercel login
   vercel
   ```

2. **Configure Environment**
   - Set `NEXT_PUBLIC_API_URL` to your backend URL (e.g., Render)
   - Enable Vercel Analytics (optional)

3. **Deploy**
   ```bash
   vercel --prod
   ```

### Manual Deployment

Build and export:
```bash
npm run build
npm start
```

Or use static export:
```bash
# In next.config.js, add: output: 'export'
npm run build
# Deploy 'out/' directory to any static host
```

## Backend Configuration

Update CORS settings in `api/main.py`:

```python
cors_origins = [
    "http://localhost:3000",           # Local development
    "https://your-app.vercel.app",     # Production
    "https://*.vercel.app"              # Preview deployments
]
```

## Troubleshooting

### Backend Connection Errors

**Error**: `Failed to fetch` or `Network error`

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/healthz`
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Ensure CORS is configured correctly
4. Check browser console for detailed errors

### Build Errors

**Error**: `Module not found` or type errors

**Solution**:
```bash
rm -rf node_modules .next
npm install
npm run build
```

### Styling Issues

**Error**: Tailwind classes not applying

**Solution**:
1. Verify `globals.css` imports in `layout.tsx`
2. Check `tailwind.config.ts` content paths
3. Restart dev server: `npm run dev`

## Contributing

1. Create a feature branch
2. Make changes with proper TypeScript types
3. Test locally: `npm run dev` and `npm run build`
4. Ensure no linting errors: `npm run lint`
5. Submit pull request

## License

MIT License - See root LICENSE file

## Links

- **Backend Repository**: [rag-pipeline](https://github.com/cbratkovics/rag-pipeline)
- **Documentation**: [README.md](../README.md)
- **Live Demo**: [Coming soon]

---

Built with ❤️ using Next.js, FastAPI, and modern AI engineering practices.
