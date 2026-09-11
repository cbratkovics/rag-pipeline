'use client'

import {
  ArrowDown,
  ArrowUpRight,
  Braces,
  Database,
  Github,
  GitMerge,
  Radio,
} from 'lucide-react'

const stages = [
  { label: 'Question', icon: Braces },
  { label: 'BM25 + vector', icon: Database },
  { label: 'RRF ranking', icon: GitMerge },
  { label: 'Grounded answer', icon: Radio },
]

export default function Hero() {
  return (
    <header className="hero-shell overflow-hidden border-b border-slate-800 text-white">
      <nav className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
        <a href="#top" className="flex items-center gap-3" aria-label="RAG Pipeline home">
          <span className="grid h-9 w-9 place-items-center rounded-lg border border-cyan-300/30 bg-cyan-300/10 font-mono text-sm font-bold text-cyan-300">
            R/
          </span>
          <span className="font-mono text-sm font-semibold tracking-tight">rag.pipeline</span>
        </a>
        <div className="flex items-center gap-5 text-sm text-slate-300">
          <a className="hidden transition-colors hover:text-white sm:block" href="#architecture">Architecture</a>
          <a className="hidden transition-colors hover:text-white sm:block" href="#workbench">Live demo</a>
          <a
            href="https://github.com/cbratkovics/rag-pipeline"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900/60 px-4 py-2 font-medium transition hover:border-cyan-400/60 hover:text-cyan-200"
          >
            <Github className="h-4 w-4" /> Source
          </a>
        </div>
      </nav>

      <div id="top" className="relative z-10 mx-auto grid max-w-7xl gap-14 px-5 pb-20 pt-14 sm:px-8 lg:grid-cols-[1.05fr_.95fr] lg:items-center lg:pb-28 lg:pt-20">
        <div>
          <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 font-mono text-xs text-emerald-300">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-300" />
            END-TO-END AI ENGINEERING CASE STUDY
          </div>
          <h1 className="max-w-4xl text-balance text-5xl font-semibold leading-[1.02] tracking-[-0.045em] sm:text-6xl lg:text-7xl">
            Retrieval you can<br />
            <span className="hero-gradient">measure, not guess.</span>
          </h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-300">
            A production-minded RAG system that fuses lexical and semantic search,
            traces every answer to its source, and makes retrieval quality visible.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <a href="#workbench" className="group inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-300 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-200">
              Explore the live workbench
              <ArrowDown className="h-4 w-4 transition-transform group-hover:translate-y-0.5" />
            </a>
            <a
              href="https://rag-pipeline-api-hksb.onrender.com/docs"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-900/50 px-5 py-3 font-semibold text-white transition hover:border-slate-500"
            >
              Inspect the API <ArrowUpRight className="h-4 w-4" />
            </a>
          </div>
          <div className="mt-10 flex flex-wrap gap-x-7 gap-y-3 font-mono text-xs text-slate-400">
            <span><b className="text-slate-100">01</b> hybrid retrieval</span>
            <span><b className="text-slate-100">02</b> RAGAS evaluation</span>
            <span><b className="text-slate-100">03</b> observable API</span>
          </div>
        </div>

        <div className="relative mx-auto w-full max-w-xl lg:mx-0">
          <div className="absolute -inset-10 rounded-full bg-cyan-400/10 blur-3xl" />
          <div className="relative overflow-hidden rounded-2xl border border-slate-700/80 bg-slate-950/80 shadow-2xl shadow-cyan-950/30 backdrop-blur">
            <div className="flex items-center justify-between border-b border-slate-800 px-5 py-3 font-mono text-[11px] text-slate-500">
              <div className="flex gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-rose-400/70" /><span className="h-2.5 w-2.5 rounded-full bg-amber-300/70" /><span className="h-2.5 w-2.5 rounded-full bg-emerald-400/70" /></div>
              TRACE / QUERY_7F2A
            </div>
            <div className="space-y-6 p-6 sm:p-8">
              <p className="font-mono text-xs text-cyan-300">$ pipeline.query(&quot;How does hybrid search improve recall?&quot;)</p>
              <div className="space-y-3">
                {stages.map(({ label, icon: Icon }, index) => (
                  <div key={label} className="flex items-center gap-4">
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-slate-700 bg-slate-900 text-slate-300"><Icon className="h-4 w-4" /></span>
                    <div className="h-px flex-1 bg-gradient-to-r from-slate-600 to-slate-800" />
                    <span className="w-32 text-sm font-medium text-slate-200">{label}</span>
                    <span className="font-mono text-[10px] text-emerald-400">{index === 3 ? 'READY' : 'PASS'}</span>
                  </div>
                ))}
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                <div className="mb-3 flex items-center justify-between text-xs"><span className="font-medium text-slate-300">Retrieval fusion</span><span className="font-mono text-cyan-300">RRF · k=60</span></div>
                <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                  <div className="rounded-md bg-slate-950 px-3 py-2 text-slate-400">BM25 <span className="float-right text-white">8 hits</span></div>
                  <div className="rounded-md bg-slate-950 px-3 py-2 text-slate-400">VECTOR <span className="float-right text-white">8 hits</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
