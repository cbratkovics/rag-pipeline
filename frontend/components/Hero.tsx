'use client'

import { Zap, TrendingUp, Shield, Sparkles, Github, FileText } from 'lucide-react'
import { MetricKPI } from '@/components/metrics/MetricKPI'

const ImpactMetrics = () => {
  // Mock sparkline data (last 20 queries)
  const latencySparkline = [520, 485, 495, 510, 490, 475, 460, 455, 450, 445, 440, 435, 430, 425, 420, 430, 440, 445, 450, 455]
  const qualitySparkline = [0.85, 0.86, 0.87, 0.88, 0.88, 0.89, 0.90, 0.91, 0.91, 0.92, 0.92, 0.91, 0.90, 0.91, 0.92, 0.92, 0.91, 0.92, 0.92, 0.92]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
      <MetricKPI
        title="Response Time"
        value={450}
        unit="ms"
        decimals={0}
        icon={Zap}
        color="text-blue-600"
        bgColor="bg-blue-50"
        delta={-15}
        deltaLabel="vs last week"
        helpText="Average P50 latency for hybrid retrieval queries"
        sparklineData={latencySparkline}
        target={500}
        targetLabel="SLA Target"
      />
      <MetricKPI
        title="Cost per Query"
        value={0.002}
        prefix="$"
        decimals={4}
        icon={TrendingUp}
        color="text-green-600"
        bgColor="bg-green-50"
        delta={-83}
        deltaLabel="via caching"
        helpText="Includes embeddings, retrieval, and LLM generation costs"
      />
      <MetricKPI
        title="Answer Quality"
        value={92}
        unit="%"
        decimals={0}
        icon={Sparkles}
        color="text-purple-600"
        bgColor="bg-purple-50"
        delta={+35}
        deltaLabel="vs baseline"
        helpText="RAGAS composite score (relevancy, faithfulness, recall)"
        sparklineData={qualitySparkline.map(v => v * 100)}
        target={85}
        targetLabel="Quality Target"
      />
      <MetricKPI
        title="Availability"
        value={99.95}
        unit="%"
        decimals={2}
        icon={Shield}
        color="text-indigo-600"
        bgColor="bg-indigo-50"
        helpText="Enterprise-grade SLA with 99.95% uptime guarantee"
        target={99.9}
        targetLabel="SLA"
      />
    </div>
  )
}

export default function Hero() {
  return (
    <section className="border-b bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="text-center">
          {/* Logo/Icon */}
          <div className="flex justify-center mb-4">
            <div className="bg-gradient-to-br from-blue-100 to-purple-100 p-3 rounded-2xl shadow-sm">
              <svg
                className="h-8 w-8 text-blue-600"
                fill="none"
                strokeWidth={2}
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"
                />
              </svg>
            </div>
          </div>

          {/* Main Title */}
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent mb-3">
            Production RAG Pipeline
          </h1>

          {/* Subtitle */}
          <p className="text-lg text-gray-700 font-medium max-w-3xl mx-auto">
            Enterprise AI Engineering • Hybrid Search • Real-time Evaluation
          </p>

          {/* Feature Badges */}
          <div className="flex flex-wrap justify-center gap-2 mt-5">
            {[
              { text: "⚡ 60% Faster", color: "border-blue-200 bg-blue-50 text-blue-700" },
              { text: "💰 83% Cost Reduction", color: "border-green-200 bg-green-50 text-green-700" },
              { text: "📊 92% Quality Score", color: "border-purple-200 bg-purple-50 text-purple-700" },
              { text: "🏢 Enterprise Ready", color: "border-indigo-200 bg-indigo-50 text-indigo-700" },
            ].map((badge) => (
              <span
                key={badge.text}
                className={`px-3 py-1.5 rounded-full border text-sm font-medium ${badge.color}`}
              >
                {badge.text}
              </span>
            ))}
          </div>

          {/* Impact Metrics */}
          <ImpactMetrics />

          {/* CTA Buttons */}
          <div className="flex flex-wrap justify-center gap-4 mt-8">
            <a
              href="https://github.com/cbratkovics/rag-pipeline"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-5 py-2.5 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors shadow-sm font-medium"
            >
              <Github className="h-5 w-5" />
              View on GitHub
            </a>
            <a
              href="/api/docs"
              target="_blank"
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm font-medium"
            >
              <FileText className="h-5 w-5" />
              API Documentation
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}
