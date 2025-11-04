export default function Hero() {
  return (
    <section className="mx-auto max-w-5xl px-4 pt-10 pb-6">
      <h1 className="text-4xl font-bold tracking-tight">
        Hybrid Retrieval with{" "}
        <span className="underline decoration-indigo-500">A/B Testing</span>{" "}
        & RAGAS Evaluation
      </h1>
      <p className="mt-3 text-gray-600">
        Production-grade RAG with BM25 + vectors fused by RRF, online A/B
        tests, and offline quality metrics. Built for observability,
        load, and repeatability.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {[
          "BM25 + Vector",
          "RRF Fusion",
          "RAGAS",
          "A/B Tests",
          "Streaming",
          "Prometheus",
        ].map((t) => (
          <span
            key={t}
            className="px-2.5 py-1 rounded-full border text-xs bg-white"
          >
            {t}
          </span>
        ))}
      </div>
      <div className="mt-6 grid grid-cols-3 gap-4">
        <Stat label="p95 Latency (ms)" value="—" />
        <Stat label="RAGAS (last run)" value="—" />
        <Stat label="AB Leader" value="—" />
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-white/60 p-3">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}
