'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Progress } from './ui/progress'
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

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          <div className="group relative">
            <Info className="h-3 w-3 text-gray-400 hover:text-gray-600 cursor-help" />
            <div className="absolute left-0 top-5 w-48 p-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-lg">
              {description}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold ${getScoreColor(value)}`}>
            {formatScore(value)}
          </span>
          {trend !== undefined && trend !== 0 && (
            <div className={`flex items-center ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend > 0 ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              <span className="text-xs ml-0.5">{Math.abs(trend * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>
      </div>
      <Progress
        value={value * 100}
        className={`h-2 ${
          value >= 0.8 ? 'bg-green-100' : value >= 0.6 ? 'bg-yellow-100' : 'bg-red-100'
        }`}
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

  // Calculate metrics from current result
  const metrics = calculateRAGASMetrics(result, question)

  // Get previous query metrics for comparison
  const previousQuery = metricsContext.queries[metricsContext.queries.length - 2]
  const previousMetrics = previousQuery
    ? calculateRAGASMetrics(previousQuery, '')
    : undefined

  return (
    <Card className="border-2 border-blue-100">
      <CardHeader>
        <CardTitle className="text-base font-semibold flex items-center justify-between">
          <span>RAGAS Quality Metrics</span>
          <div className={`text-2xl font-bold ${getScoreColor(metrics.overall_score || 0)}`}>
            {formatScore(metrics.overall_score || 0)}
          </div>
        </CardTitle>
        <p className="text-xs text-gray-500 mt-1">
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
      </CardContent>
    </Card>
  )
}
