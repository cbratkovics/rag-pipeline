'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Progress } from './ui/progress'
import { Badge } from './ui/badge'
import { HoverCard, HoverCardContent, HoverCardTrigger } from './ui/hover-card'
import { Info, TrendingUp, TrendingDown } from 'lucide-react'
import { calculateRAGASMetrics, getScoreColor, formatScore } from '@/lib/ragas-utils'
import { useMetrics } from '@/contexts/MetricsContext'
import type { QueryResponse } from '@/types'

interface RAGASScoresProps {
  result?: QueryResponse
  question?: string
}

interface MetricRowProps {
  label: string
  value: number
  description: string
  previousValue?: number
}

function MetricRow({ label, value, description, previousValue }: MetricRowProps) {
  const trend = previousValue !== undefined && previousValue !== 0
    ? value - previousValue
    : undefined

  // Helper to get progress bar color based on score
  const getProgressColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-500'
    if (score >= 0.6) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="space-y-2 p-3 rounded-lg bg-gray-50/50 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-700">{label}</span>
          <HoverCard>
            <HoverCardTrigger asChild>
              <button className="text-gray-400 hover:text-gray-600 transition-colors">
                <Info className="h-3.5 w-3.5" />
              </button>
            </HoverCardTrigger>
            <HoverCardContent className="w-72">
              <p className="text-sm text-gray-700">{description}</p>
            </HoverCardContent>
          </HoverCard>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xl font-bold ${getScoreColor(value)} tabular-nums`}>
            {formatScore(value)}
          </span>
          {trend !== undefined && trend !== 0 && (
            <Badge
              variant="outline"
              className={`flex items-center gap-1 ${
                trend > 0
                  ? 'bg-green-50 text-green-700 border-green-200'
                  : 'bg-red-50 text-red-700 border-red-200'
              }`}
            >
              {trend > 0 ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              <span className="text-xs font-semibold">
                {trend > 0 ? '+' : ''}{Math.abs(trend * 100).toFixed(0)}%
              </span>
            </Badge>
          )}
        </div>
      </div>
      <Progress
        value={value * 100}
        className={`h-2.5 ${
          value >= 0.8 ? 'bg-green-100' : value >= 0.6 ? 'bg-yellow-100' : 'bg-red-100'
        }`}
        indicatorClassName={getProgressColor(value)}
      />
    </div>
  )
}

export function RAGASScores({ result, question = '' }: RAGASScoresProps) {
  const metricsContext = useMetrics()

  if (!result) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            RAGAS Quality Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500 text-center py-8">
            Run a query to see quality metrics
          </p>
        </CardContent>
      </Card>
    )
  }

  // First check if backend provides real RAGAS metrics
  // If not, calculate fallback metrics from available data
  const usingBackendMetrics = !!result.evaluation_metrics
  const metrics = result.evaluation_metrics || calculateRAGASMetrics(result, question)

  // Get previous query metrics for comparison
  const previousQuery = metricsContext.queries[metricsContext.queries.length - 2]
  const previousMetrics = previousQuery
    ? (previousQuery.evaluation_metrics || calculateRAGASMetrics(previousQuery, ''))
    : undefined

  return (
    <Card className="border-2 border-purple-100 bg-gradient-to-br from-purple-50/30 to-white">
      <CardHeader>
        <div className="flex items-center justify-between mb-2">
          <CardTitle className="text-base font-semibold">
            RAGAS Quality Metrics
          </CardTitle>
          <Badge
            className={`text-base font-bold px-3 py-1 ${
              (metrics.overall_score || 0) >= 0.8
                ? 'bg-green-500 text-white'
                : (metrics.overall_score || 0) >= 0.6
                ? 'bg-yellow-500 text-white'
                : 'bg-red-500 text-white'
            }`}
          >
            {formatScore(metrics.overall_score || 0)}
          </Badge>
        </div>
        <p className="text-xs text-gray-600">
          AI-powered quality assessment of retrieval and generation
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        <MetricRow
          label="Context Relevancy"
          value={metrics.context_relevancy || 0}
          description="How relevant are the retrieved contexts to the query?"
          previousValue={previousMetrics?.context_relevancy}
        />

        <MetricRow
          label="Answer Faithfulness"
          value={metrics.answer_faithfulness || 0}
          description="Is the answer grounded in the retrieved contexts?"
          previousValue={previousMetrics?.answer_faithfulness}
        />

        <MetricRow
          label="Answer Relevancy"
          value={metrics.answer_relevancy || 0}
          description="How well does the answer address the question?"
          previousValue={previousMetrics?.answer_relevancy}
        />

        <MetricRow
          label="Context Recall"
          value={metrics.context_recall || 0}
          description="Did we retrieve all relevant information?"
          previousValue={previousMetrics?.context_recall}
        />

        {/* Overall Score Summary */}
        <div className="pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-gray-700">Overall Score</span>
            <span className={`text-2xl font-bold ${getScoreColor(metrics.overall_score || 0)}`}>
              {formatScore(metrics.overall_score || 0)}
            </span>
          </div>
          <Progress
            value={(metrics.overall_score || 0) * 100}
            className={`h-3 mt-2 ${
              (metrics.overall_score || 0) >= 0.8
                ? 'bg-green-100'
                : (metrics.overall_score || 0) >= 0.6
                ? 'bg-yellow-100'
                : 'bg-red-100'
            }`}
            indicatorClassName={
              (metrics.overall_score || 0) >= 0.8
                ? 'bg-green-500'
                : (metrics.overall_score || 0) >= 0.6
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }
          />
        </div>

        {/* Performance indicator */}
        {(metrics.overall_score || 0) >= 0.9 && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-xs text-green-700 font-medium text-center">
              Excellent quality! This response meets production standards.
            </p>
          </div>
        )}
        {(metrics.overall_score || 0) < 0.6 && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-xs text-yellow-700 font-medium text-center">
              Quality could be improved. Consider refining the query or documents.
            </p>
          </div>
        )}

        {/* Info note if using fallback metrics */}
        {!usingBackendMetrics && (
          <div className="pt-3 border-t border-gray-200">
            <p className="text-xs text-gray-500 italic text-center">
              Quality scores are estimated from response data. Enable backend RAGAS evaluation for precise metrics.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
