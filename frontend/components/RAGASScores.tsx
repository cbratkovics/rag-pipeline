'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Info } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import type { RAGASMetrics } from '@/types'

interface RAGASScoresProps {
  metrics?: RAGASMetrics
}

export function RAGASScores({ metrics }: RAGASScoresProps) {
  const [liveMetrics, setLiveMetrics] = useState<any>(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/metrics/ragas`)
        if (res.ok) {
          const data = await res.json()
          setLiveMetrics(data)
        }
      } catch (error) {
        console.error('Failed to fetch RAGAS metrics:', error)
      }
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 60000)
    return () => clearInterval(interval)
  }, [])
  // Mock RAGAS metrics for demo purposes
  // In production, these would come from the backend
  const defaultMetrics: RAGASMetrics = {
    context_relevancy: 0.85,
    answer_faithfulness: 0.92,
    answer_relevancy: 0.88,
    context_recall: 0.79,
    overall_score: 0.86,
  }

  const ragasMetrics = metrics || defaultMetrics

  const metricDefinitions = [
    {
      key: 'context_relevancy' as keyof RAGASMetrics,
      label: 'Context Relevancy',
      description: 'How relevant the retrieved contexts are to the question',
      threshold: 0.7,
    },
    {
      key: 'answer_faithfulness' as keyof RAGASMetrics,
      label: 'Answer Faithfulness',
      description: 'How faithful the answer is to the given context',
      threshold: 0.8,
    },
    {
      key: 'answer_relevancy' as keyof RAGASMetrics,
      label: 'Answer Relevancy',
      description: 'How relevant the answer is to the question',
      threshold: 0.8,
    },
    {
      key: 'context_recall' as keyof RAGASMetrics,
      label: 'Context Recall',
      description: 'How much of the ground truth is captured in the context',
      threshold: 0.7,
    },
  ]

  const getScoreColor = (score: number, threshold: number): string => {
    if (score >= threshold) return 'bg-green-600'
    if (score >= threshold * 0.8) return 'bg-amber-600'
    return 'bg-red-600'
  }

  const getScoreLabel = (score: number, threshold: number): string => {
    if (score >= threshold) return 'Good'
    if (score >= threshold * 0.8) return 'Fair'
    return 'Poor'
  }

  const overallScore = ragasMetrics.overall_score || 0
  const overallColor = overallScore >= 0.8 ? 'success' : overallScore >= 0.6 ? 'warning' : 'destructive'

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">RAGAS Evaluation</CardTitle>
            <CardDescription>
              Automated quality assessment metrics
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Overall:</span>
            <Badge variant={overallColor} className="text-lg px-3 py-1">
              {(overallScore * 100).toFixed(0)}%
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {metricDefinitions.map((metric) => {
          const score = ragasMetrics[metric.key] || 0
          const scoreColor = getScoreColor(score, metric.threshold)
          const scoreLabel = getScoreLabel(score, metric.threshold)

          return (
            <div key={metric.key} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{metric.label}</span>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <Info className="h-3 w-3 text-gray-400" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="max-w-xs text-xs">{metric.description}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    {scoreLabel}
                  </Badge>
                  <span className="text-sm font-semibold">
                    {score.toFixed(2)}
                  </span>
                </div>
              </div>

              <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`absolute inset-y-0 left-0 ${scoreColor} transition-all duration-500`}
                  style={{ width: `${score * 100}%` }}
                />
                {/* Threshold indicator */}
                <div
                  className="absolute inset-y-0 w-0.5 bg-gray-400 opacity-50"
                  style={{ left: `${metric.threshold * 100}%` }}
                />
              </div>

              <div className="flex justify-between text-xs text-gray-400">
                <span>0.0</span>
                <span className="text-gray-500">Target: {metric.threshold}</span>
                <span>1.0</span>
              </div>
            </div>
          )
        })}

        {!metrics && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-xs text-blue-800">
              <strong>Demo Data:</strong> These are simulated RAGAS scores.
              In production, scores are calculated by the backend evaluation pipeline.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
