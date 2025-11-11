'use client'

import { useState } from 'react'
import { Button } from './ui/button'
import { Card } from './ui/card'
import type { QueryParams, ABVariant } from '@/types'

interface QueryInterfaceProps {
  onSubmit: (question: string, params: QueryParams, variant: ABVariant) => void
  isLoading?: boolean
}

export function QueryInterface({ onSubmit, isLoading }: QueryInterfaceProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      onSubmit(query, {
        k: 4,
        top_k_bm25: 8,
        top_k_vec: 8,
        rrf_k: 60,
        provider: 'stub'
      }, 'baseline')
    }
  }

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
          className="w-full px-4 py-2 border rounded-lg"
          disabled={isLoading}
        />
        <Button type="submit" disabled={isLoading || !query.trim()}>
          {isLoading ? 'Loading...' : 'Search'}
        </Button>
      </form>
    </Card>
  )
}
