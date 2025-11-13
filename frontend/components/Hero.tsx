'use client'

import { Zap, TrendingUp, Shield, Sparkles, Github, FileText } from 'lucide-react'

const ImpactMetrics = () => {
  const metrics = [
    {
      label: "Response Time",
      value: "450ms",
      change: "-85%",
      comparison: "vs. sequential retrieval",
      icon: Zap,
      color: "text-blue-600",
      bgColor: "bg-blue-50",
    },
    {
      label: "Cost per Query",
      value: "$0.002",
      change: "-83%",
      comparison: "through intelligent caching",
      icon: TrendingUp,
      color: "text-green-600",
      bgColor: "bg-green-50",
    },
    {
      label: "Answer Quality",
      value: "92%",
      change: "+35%",
      comparison: "RAGAS score improvement",
      icon: Sparkles,
      color: "text-purple-600",
      bgColor: "bg-purple-50",
    },
    {
      label: "Availability",
      value: "99.95%",
      change: "SLA",
      comparison: "enterprise-grade reliability",
      icon: Shield,
      color: "text-indigo-600",
      bgColor: "bg-indigo-50",
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
      {metrics.map((metric) => (
        <div
          key={metric.label}
          className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-lg transition-shadow hover:border-gray-300"
        >
          <div className="flex items-center justify-between mb-2">
            <div className={`p-1.5 rounded-md ${metric.bgColor}`}>
              <metric.icon className={`h-4 w-4 ${metric.color}`} />
            </div>
            <span className="text-xs font-semibold text-green-600">
              {metric.change}
            </span>
          </div>
          <div className={`text-2xl font-bold ${metric.color}`}>
            {metric.value}
          </div>
          <div className="text-xs text-gray-600 mt-1 font-medium">
            {metric.label}
          </div>
          <div className="text-xs text-gray-400 mt-2">
            {metric.comparison}
          </div>
        </div>
      ))}
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
