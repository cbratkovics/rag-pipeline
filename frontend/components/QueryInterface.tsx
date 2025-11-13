'use client'

import { useState } from 'react'
import { Button } from './ui/button'
import { Card } from './ui/card'
import { Badge } from './ui/badge'
import { Sparkles } from 'lucide-react'
import type { QueryParams, ABVariant } from '@/types'

interface QueryInterfaceProps {
  onSubmit: (question: string, params: QueryParams, variant: ABVariant) => void
  isLoading?: boolean
}

const DEMO_QUERIES = [
  "What is Retrieval-Augmented Generation?",
  "Explain the difference between BM25 and vector search",
  "How does Reciprocal Rank Fusion work?",
  "What are RAGAS evaluation metrics?",
  "Best practices for chunking documents in RAG"
]

export function QueryInterface({ onSubmit, isLoading }: QueryInterfaceProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      onSubmit(query, {
        k: 4,
        top_k_bm25: 8,
        top_k_vec: 8,
        rrf_k: 60
      }, 'baseline')
    }
  }

  const handleDemoQuery = (demoQuery: string) => {
    setQuery(demoQuery)
    onSubmit(demoQuery, {
      k: 4,
      top_k_bm25: 8,
      top_k_vec: 8,
      rrf_k: 60
    }, 'baseline')
  }

  return (
    <Card className="p-6 border-2 shadow-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about RAG, search algorithms, or AI..."
            className="w-full px-5 py-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all outline-none text-base font-medium placeholder:text-gray-400"
            disabled={isLoading}
          />
          <div className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
            <kbd className="px-2.5 py-1.5 text-xs bg-gray-100 rounded-md border border-gray-200 font-semibold">
              Enter
            </kbd>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <Button
            type="submit"
            disabled={isLoading || !query.trim()}
            size="lg"
            className="px-10 py-6 text-base font-semibold shadow-lg hover:shadow-xl transition-all"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Searching...
              </span>
            ) : (
              'Search'
            )}
          </Button>
        </div>
      </form>

      {/* Demo Queries */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-medium text-gray-700">Try these examples:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {DEMO_QUERIES.map((demoQuery, index) => (
            <button
              key={index}
              onClick={() => handleDemoQuery(demoQuery)}
              disabled={isLoading}
              className="text-xs px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-full border border-blue-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {demoQuery}
            </button>
          ))}
        </div>
      </div>
    </Card>
  )
}
