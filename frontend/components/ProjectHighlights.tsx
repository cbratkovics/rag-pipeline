import { Activity, FlaskConical, GitMerge, ServerCog } from 'lucide-react'

const capabilities = [
  {
    number: '01', icon: GitMerge, title: 'Retrieval, engineered',
    body: 'BM25 catches exact language. Dense embeddings capture intent. Reciprocal Rank Fusion combines both without brittle score normalization.',
    tag: 'BM25 · ChromaDB · RRF',
  },
  {
    number: '02', icon: FlaskConical, title: 'Quality, quantified',
    body: 'RAGAS scoring and A/B hooks turn prompt and retrieval changes into comparable experiments—not subjective demos.',
    tag: 'Faithfulness · Recall · Relevancy',
  },
  {
    number: '03', icon: Activity, title: 'Operations, visible',
    body: 'Structured logs, Prometheus metrics, health checks, budgets, retries, and cache telemetry expose how the system behaves under load.',
    tag: 'Prometheus · OpenTelemetry · Redis',
  },
  {
    number: '04', icon: ServerCog, title: 'Delivery, included',
    body: 'Typed FastAPI contracts, a Next.js client, container orchestration, Kubernetes manifests, and load tests form one deployable system.',
    tag: 'FastAPI · Next.js · Docker',
  },
]

export function ProjectHighlights() {
  return (
    <section id="architecture" className="border-b border-slate-200 bg-[#f4f5f2]">
      <div className="mx-auto max-w-7xl px-5 py-20 sm:px-8">
        <div className="grid gap-8 lg:grid-cols-[.65fr_1.35fr] lg:items-end">
          <div>
            <p className="section-kicker">UNDER THE HOOD</p>
            <h2 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-slate-950 sm:text-5xl">Not another<br />chat wrapper.</h2>
          </div>
          <p className="max-w-2xl text-lg leading-8 text-slate-600">The portfolio story is the system around the model: retrieval tradeoffs, measurable evaluation, failure-aware infrastructure, and a UI that exposes the evidence.</p>
        </div>
        <div className="mt-12 grid gap-px overflow-hidden rounded-2xl border border-slate-200 bg-slate-200 md:grid-cols-2">
          {capabilities.map(({ number, icon: Icon, title, body, tag }) => (
            <article key={number} className="group bg-white p-7 transition-colors hover:bg-cyan-50/40 sm:p-9">
              <div className="flex items-center justify-between"><span className="font-mono text-xs text-slate-400">/{number}</span><Icon className="h-5 w-5 text-slate-400 transition-colors group-hover:text-cyan-600" /></div>
              <h3 className="mt-10 text-xl font-semibold tracking-tight text-slate-950">{title}</h3>
              <p className="mt-3 leading-7 text-slate-600">{body}</p>
              <p className="mt-7 font-mono text-[11px] uppercase tracking-wider text-cyan-700">{tag}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
