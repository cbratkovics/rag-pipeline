'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, AlertCircle } from 'lucide-react'
import type { QueryResponse } from '@/types'
import { getConfidenceColor, getConfidenceLabel, parseScoreAverage } from '@/lib/utils'

interface ResultsDisplayProps {
  result: QueryResponse
}

export function ResultsDisplay({ result }: ResultsDisplayProps) {
  const [displayedText, setDisplayedText] = useState('')
  const [isAnimating, setIsAnimating] = useState(true)

  // Typing animation for answer
  useEffect(() => {
    setDisplayedText('')
    setIsAnimating(true)

    let currentIndex = 0
    const answer = result.answer

    const interval = setInterval(() => {
      if (currentIndex < answer.length) {
        setDisplayedText(answer.slice(0, currentIndex + 1))
        currentIndex++
      } else {
        setIsAnimating(false)
        clearInterval(interval)
      }
    }, 10) // Fast typing speed

    return () => clearInterval(interval)
  }, [result.answer])

  // Calculate confidence score from scores
  const confidenceScore = parseScoreAverage(result.scores)
  const confidenceColor = getConfidenceColor(confidenceScore)
  const confidenceLabel = getConfidenceLabel(confidenceScore)

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4 animate-fade-in">
      {/* Answer Card */}
      <Card>
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-4">
          <div className="space-y-1">
            <CardTitle className="text-xl">Answer</CardTitle>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <span className="text-sm text-gray-500">
                Generated in {result.latency_ms.toFixed(0)}ms
              </span>
            </div>
          </div>

          {/* Confidence Badge */}
          <div className="flex items-center gap-2">
            <Badge className={confidenceColor}>
              {confidenceLabel} Confidence
            </Badge>
            <Badge variant="secondary">
              {(confidenceScore * 100).toFixed(0)}%
            </Badge>
          </div>
        </CardHeader>

        <CardContent>
          <div className="prose prose-sm max-w-none">
            <p className="text-gray-900 leading-relaxed whitespace-pre-wrap">
              {displayedText}
              {isAnimating && (
                <span className="inline-block w-1 h-5 bg-blue-600 ml-1 animate-pulse" />
              )}
            </p>
          </div>

          {/* Timing Breakdown */}
          {result.timing && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="grid grid-cols-3 gap-4 text-sm">
                {result.timing.retrieval_ms !== undefined && (
                  <div>
                    <p className="text-gray-500">Retrieval</p>
                    <p className="font-semibold">{result.timing.retrieval_ms.toFixed(0)}ms</p>
                  </div>
                )}
                {result.timing.generation_ms !== undefined && (
                  <div>
                    <p className="text-gray-500">Generation</p>
                    <p className="font-semibold">{result.timing.generation_ms.toFixed(0)}ms</p>
                  </div>
                )}
                <div>
                  <p className="text-gray-500">Total</p>
                  <p className="font-semibold">{result.latency_ms.toFixed(0)}ms</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Retrieval Scores */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Retrieval Scores</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(result.scores).map(([method, score]) => (
              <div key={method} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium capitalize">{method}</span>
                  <span className="text-gray-500">{score.toFixed(3)}</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-500"
                    style={{ width: `${Math.min(score * 100, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 flex items-center gap-2 text-xs text-gray-500">
            <AlertCircle className="h-3 w-3" />
            <span>Higher scores indicate better relevance</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
