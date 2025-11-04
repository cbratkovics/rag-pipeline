'use client'

import { useState } from 'react'
import { Search, Settings, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { QueryParams, ABVariant } from '@/types'

interface QueryInterfaceProps {
  onSubmit: (question: string, params: QueryParams, variant: ABVariant) => void
  isLoading: boolean
}

export function QueryInterface({ onSubmit, isLoading }: QueryInterfaceProps) {
  const [question, setQuestion] = useState('Explain the differences between semantic search and keyword search in modern RAG systems')
  const [showAdvanced, setShowAdvanced] = useState(true)
  const [variant, setVariant] = useState<ABVariant>('auto')

  // Query parameters with defaults matching backend
  const [params, setParams] = useState<QueryParams>({
    k: 4,
    top_k_bm25: 8,
    top_k_vec: 8,
    rrf_k: 60,
    provider: 'stub',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (question.trim()) {
      onSubmit(question.trim(), params, variant)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit(e)
    }
  }

  const variantOptions: { value: ABVariant; label: string; description: string }[] = [
    { value: 'auto', label: 'Auto', description: 'Automatic assignment' },
    { value: 'baseline', label: 'Baseline', description: 'Standard retrieval' },
    { value: 'reranked', label: 'Reranked', description: 'With cross-encoder' },
    { value: 'hybrid', label: 'Hybrid', description: 'Advanced fusion' },
  ]

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      {/* Main Query Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <Input
            type="text"
            placeholder="Ask a question about your documents..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={handleKeyPress}
            className="pl-10 pr-4 h-14 text-lg"
            disabled={isLoading}
            autoFocus
          />
        </div>

        <div className="flex items-center justify-between gap-4">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="gap-2"
          >
            <Settings className="h-4 w-4" />
            {showAdvanced ? 'Hide' : 'Show'} Settings
          </Button>

          <div className="flex items-center gap-4">
            <Button
              type="submit"
              disabled={!question.trim() || isLoading}
              className="gap-2"
            >
              {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              {isLoading ? 'Searching...' : 'Search'}
            </Button>
          </div>
        </div>
      </form>

      {/* Advanced Settings */}
      {showAdvanced && (
        <Card className="animate-slide-in">
          <CardHeader>
            <CardTitle className="text-lg">Advanced Settings</CardTitle>
            <CardDescription>
              Fine-tune retrieval and generation parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* A/B Testing Variant */}
            <div className="space-y-2">
              <Label>A/B Test Variant</Label>
              <div className="flex gap-2">
                {variantOptions.map((option) => (
                  <Button
                    key={option.value}
                    type="button"
                    variant={variant === option.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setVariant(option.value)}
                    className="flex-1"
                  >
                    {option.label}
                  </Button>
                ))}
              </div>
              <p className="text-xs text-gray-500">
                {variantOptions.find(v => v.value === variant)?.description}
              </p>
            </div>

            {/* Retrieval Settings */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="k">
                  Final Results (k)
                  <Badge variant="secondary" className="ml-2">
                    {params.k}
                  </Badge>
                </Label>
                <Input
                  id="k"
                  type="number"
                  min={1}
                  max={20}
                  value={params.k}
                  onChange={(e) => setParams({ ...params, k: parseInt(e.target.value) || 4 })}
                />
                <p className="text-xs text-gray-500">Final number of contexts to use</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="rrf_k">
                  RRF K Parameter
                  <Badge variant="secondary" className="ml-2">
                    {params.rrf_k}
                  </Badge>
                </Label>
                <Input
                  id="rrf_k"
                  type="number"
                  min={1}
                  max={100}
                  value={params.rrf_k}
                  onChange={(e) => setParams({ ...params, rrf_k: parseInt(e.target.value) || 60 })}
                />
                <p className="text-xs text-gray-500">Reciprocal rank fusion parameter</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="top_k_bm25">
                  BM25 Results
                  <Badge variant="secondary" className="ml-2">
                    {params.top_k_bm25}
                  </Badge>
                </Label>
                <Input
                  id="top_k_bm25"
                  type="number"
                  min={1}
                  max={50}
                  value={params.top_k_bm25}
                  onChange={(e) => setParams({ ...params, top_k_bm25: parseInt(e.target.value) || 8 })}
                />
                <p className="text-xs text-gray-500">Keyword search results</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="top_k_vec">
                  Vector Results
                  <Badge variant="secondary" className="ml-2">
                    {params.top_k_vec}
                  </Badge>
                </Label>
                <Input
                  id="top_k_vec"
                  type="number"
                  min={1}
                  max={50}
                  value={params.top_k_vec}
                  onChange={(e) => setParams({ ...params, top_k_vec: parseInt(e.target.value) || 8 })}
                />
                <p className="text-xs text-gray-500">Semantic search results</p>
              </div>
            </div>

            {/* LLM Provider */}
            <div className="space-y-2">
              <Label>LLM Provider</Label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={params.provider === 'stub' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setParams({ ...params, provider: 'stub' })}
                >
                  Stub (Fast)
                </Button>
                <Button
                  type="button"
                  variant={params.provider === 'openai' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setParams({ ...params, provider: 'openai' })}
                >
                  OpenAI (Production)
                </Button>
              </div>
              <p className="text-xs text-gray-500">
                Stub uses templated responses. OpenAI requires API key.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Keyboard Shortcut Hint */}
      <p className="text-xs text-gray-500 text-center">
        Press <kbd className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-xs">⌘/Ctrl + Enter</kbd> to search
      </p>
    </div>
  )
}
