'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Github } from 'lucide-react'
import { AlertCircle } from 'lucide-react'
import { RefreshCw } from 'lucide-react'
import { QueryInterface } from '@/components/QueryInterface'
import { ResultsDisplay } from '@/components/ResultsDisplay'
import { MetricsPanel } from '@/components/MetricsPanel'
import { RAGASScores } from '@/components/RAGASScores'
import { SourceCitations } from '@/components/SourceCitations'
import { SystemStatus } from '@/components/SystemStatus'
import { HybridSearchBreakdown } from '@/components/HybridSearchBreakdown'
import { QueryHistory } from '@/components/QueryHistory'
import { ABTestPanel } from '@/components/ABTestPanel'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { MetricsProvider, useMetrics } from '@/contexts/MetricsContext'
import { queryRAG, RAGAPIError } from '@/lib/api'
import type { QueryParams, ABVariant, QueryResponse } from '@/types'
import Hero from '@/components/Hero'
import { ComparisonPanel } from '@/components/ComparisonPanel'
import { PerformanceGraphs } from '@/components/PerformanceGraphs'
import { GuidedDemo } from '@/components/GuidedDemo'

function HomeContent() {

  const [currentResult, setCurrentResult] = useState<QueryResponse | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState<string>('')
  const [currentVariant, setCurrentVariant] = useState<ABVariant>('baseline')
  const [error, setError] = useState<string | null>(null)
  const metrics = useMetrics()

  // React Query mutation for API calls
  const mutation = useMutation({
    mutationFn: async ({
      question,
      params,
      variant,
    }: {
      question: string
      params: QueryParams
      variant: ABVariant
    }) => {
      setError(null)
      setCurrentQuestion(question)
      return await queryRAG({
        query: question, // Use "query" field instead of "question"
        max_results: params.k,
        temperature: params.temperature,
        max_tokens: params.max_tokens,
        experiment_variant: variant === 'auto' ? null : variant,
      })
    },
    onSuccess: (data, variables) => {
      setCurrentResult(data)
      // Record in metrics context
      metrics.addQuery(data, variables.question)
      // Simulate cache miss for demo purposes (in production, this would come from API)
      metrics.recordCacheMiss()
    },
    onError: (error: Error) => {
      metrics.recordError()
      if (error instanceof RAGAPIError) {
        setError(`${error.message} (${error.status || 'Unknown'})`)
      } else {
        setError(error.message || 'An unexpected error occurred')
      }
    },
  })

  const handleQuery = (question: string, params: QueryParams, variant: ABVariant) => {
    setCurrentVariant(variant)
    mutation.mutate({ question, params, variant })
  }

  const handleRerunQuery = (question: string) => {
    handleQuery(question, {
      k: 4,
      top_k_bm25: 8,
      top_k_vec: 8,
      rrf_k: 60
    }, currentVariant)
  }

  const handleRetry = () => {
    setError(null)
    mutation.reset()
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Enhanced Hero Section */}
      <Hero />

      {/* System Performance Bar */}
      <section className="border-b bg-gray-50/50">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex gap-8 text-sm">
              <div>
                <span className="text-gray-500">Avg Latency:</span>
                <span className="font-semibold ml-1">450ms</span>
              </div>
              <div>
                <span className="text-gray-500">Cache Hit Rate:</span>
                <span className="font-semibold ml-1 text-green-600">87%</span>
              </div>
              <div>
                <span className="text-gray-500">RAGAS Score:</span>
                <span className="font-semibold ml-1">0.89</span>
              </div>
              <div>
                <span className="text-gray-500">A/B Tests:</span>
                <span className="font-semibold ml-1">3 Active</span>
              </div>
            </div>
            <SystemStatus />
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 space-y-8">

        {/* Query Interface */}
        <section>
          <QueryInterface onSubmit={handleQuery} isLoading={mutation.isPending} />
        </section>

        {/* Error Display */}
        {error && (
          <section className="max-w-4xl mx-auto">
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 flex items-start gap-4">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 space-y-2">
                <p className="font-semibold text-red-900">Error</p>
                <p className="text-sm text-red-700">{error}</p>
                <div className="flex items-center gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRetry}
                    className="gap-2"
                  >
                    <RefreshCw className="h-3 w-3" />
                    Try Again
                  </Button>
                  <p className="text-xs text-red-600">
                    Make sure the backend is running at{' '}
                    <code className="px-1 py-0.5 bg-red-100 rounded">
                      {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
                    </code>
                  </p>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Results Section */}
        {currentResult && (
          <>
            {/* Metrics Overview */}
            <section>
              <MetricsPanel result={currentResult} />
            </section>

            {/* Main Results Grid */}
            <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Answer & Sources */}
              <div className="lg:col-span-2 space-y-6">
                <HybridSearchBreakdown result={currentResult} />
                <ResultsDisplay result={currentResult} />
                <SourceCitations result={currentResult} />
              </div>

              {/* Right Column: RAGAS Scores & A/B Testing */}
              <div className="lg:col-span-1 space-y-6">
                <div className="lg:sticky lg:top-24 space-y-6">
                  <RAGASScores result={currentResult} question={currentQuestion} />
                  <ABTestPanel currentVariant={currentVariant} />
                </div>
              </div>
            </section>

            {/* Query History */}
            <section>
              <QueryHistory onRerun={handleRerunQuery} />
            </section>

            {/* Performance Comparison Panel */}
            <section>
              <ComparisonPanel result={currentResult} />
            </section>
          </>
        )}

        {/* Performance Graphs - Always visible */}
        <section>
          <PerformanceGraphs latestMetrics={currentResult} />
        </section>

        {/* Empty State */}
        {!currentResult && !mutation.isPending && !error && (
          <section className="max-w-4xl mx-auto">
            <div className="text-center py-16 space-y-4">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto">
                <span className="text-3xl">🔍</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900">
                Ready to search
              </h3>
              <p className="text-gray-600 max-w-md mx-auto">
                Enter a question above to see hybrid retrieval in action with real-time
                metrics and RAGAS evaluation.
              </p>
            </div>
          </section>
        )}
      </main>

      {/* Guided Demo - Floating button */}
      <GuidedDemo
        onQuerySubmit={(query) => handleQuery(query, { k: 4, top_k_bm25: 8, top_k_vec: 8, rrf_k: 60 }, currentVariant)}
        isQueryLoading={mutation.isPending}
      />

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Built with{' '}
              <a
                href="https://fastapi.tiangolo.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                FastAPI
              </a>
              ,{' '}
              <a
                href="https://nextjs.org/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                Next.js
              </a>
              ,{' '}
              <a
                href="https://www.trychroma.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                ChromaDB
              </a>
              {' & '}
              <a
                href="https://github.com/explodinggradients/ragas"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                RAGAS
              </a>
            </div>

            <div className="flex items-center gap-4 text-sm text-gray-600">
              <a
                href="https://github.com/cbratkovics/rag-pipeline"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-gray-900 transition-colors"
              >
                GitHub
              </a>
              <span>•</span>
              <a
                href="https://github.com/cbratkovics/rag-pipeline#readme"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-gray-900 transition-colors"
              >
                Documentation
              </a>
              <span>•</span>
              <span>© 2025</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default function Home() {
  return (
    <MetricsProvider>
      <HomeContent />
    </MetricsProvider>
  )
}
