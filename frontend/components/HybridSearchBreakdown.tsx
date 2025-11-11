'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { Info } from 'lucide-react'
import type { QueryResponse } from '@/types'

interface HybridSearchBreakdownProps {
  result?: QueryResponse
}

export function HybridSearchBreakdown({ result }: HybridSearchBreakdownProps) {
  if (!result || !result.scores) {
    return null
  }

  const { hybrid = 0, bm25 = 0, vector = 0 } = result.scores

  // Calculate contributions (as percentages)
  const total = bm25 + vector
  const bm25Percent = total > 0 ? (bm25 / total) * 100 : 50
  const vectorPercent = total > 0 ? (vector / total) * 100 : 50

  // Determine which method contributed more
  const dominantMethod = bm25 > vector ? 'BM25' : vector > bm25 ? 'Vector' : 'Equal'

  return (
    <Card className="border-2 border-blue-100 bg-gradient-to-br from-blue-50 to-white">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold">Hybrid Search Breakdown</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-white">
              Reciprocal Rank Fusion
            </Badge>
            <div className="group relative">
              <Info className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help" />
              <div className="absolute right-0 top-6 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-lg">
                RRF combines BM25 (keyword search) and vector embeddings (semantic search) to
                provide optimal retrieval. Higher scores indicate better relevance.
              </div>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Hybrid Score */}
        <div className="text-center p-4 bg-white rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Hybrid Score</p>
          <p className="text-4xl font-bold text-blue-600">{hybrid.toFixed(3)}</p>
        </div>

        {/* BM25 Score */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="bg-purple-100 text-purple-700 border-purple-200">
                BM25 Keyword Search
              </Badge>
              {dominantMethod === 'BM25' && (
                <span className="text-xs text-purple-600 font-medium">Dominant</span>
              )}
            </div>
            <span className="text-sm font-semibold text-gray-700">{bm25.toFixed(3)}</span>
          </div>
          <Progress value={bm25Percent} className="h-3 bg-gray-100" />
          <p className="text-xs text-gray-500">{bm25Percent.toFixed(1)}% contribution</p>
        </div>

        {/* Vector Score */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="bg-green-100 text-green-700 border-green-200">
                Vector Semantic Search
              </Badge>
              {dominantMethod === 'Vector' && (
                <span className="text-xs text-green-600 font-medium">Dominant</span>
              )}
            </div>
            <span className="text-sm font-semibold text-gray-700">{vector.toFixed(3)}</span>
          </div>
          <Progress value={vectorPercent} className="h-3 bg-gray-100" />
          <p className="text-xs text-gray-500">{vectorPercent.toFixed(1)}% contribution</p>
        </div>

        {/* Explanation */}
        <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-100">
          <p className="text-xs text-gray-700">
            <span className="font-semibold">How it works:</span> BM25 finds documents with matching
            keywords, while vector search finds semantically similar content. RRF combines both
            rankings to give you the best of both worlds.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
