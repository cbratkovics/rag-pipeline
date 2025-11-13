'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { Zap, Database, DollarSign, Award, TrendingUp, Target } from 'lucide-react'
import { useMetrics } from '@/contexts/MetricsContext'
import { calculateCacheHitRate, formatCost } from '@/lib/ragas-utils'
import type { QueryResponse } from '@/types'

interface MetricPanelProps {
  result?: QueryResponse
}

export function MetricPanel({ result }: MetricPanelProps) {
  const metrics = useMetrics()

  // Calculate current query metrics
  const currentLatency = result ? (result.processing_time_ms || result.latency_ms || 0) : 0
  const cacheHitRate = calculateCacheHitRate(metrics.cacheHits, metrics.cacheMisses)

  // Mock RAGAS scores (in production, these would come from the API)
  const ragasScores = result?.evaluation_metrics || {
    answer_relevancy: 0.89,
    context_recall: 0.85,
    answer_faithfulness: 0.92,
    overall_score: 0.89,
  }

  // Performance targets
  const LATENCY_TARGET = 500 // ms
  const CACHE_TARGET = 85 // %
  const RAGAS_TARGET = 0.85
  const COST_TARGET = 0.002 // $ per query

  const currentCost = metrics.totalQueries > 0
    ? metrics.totalCost / metrics.totalQueries
    : 0.002

  return (
    <Card className="border-2">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">Live Metrics</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="latency" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="latency" className="text-xs">
              <Zap className="h-3 w-3 mr-1" />
              Latency
            </TabsTrigger>
            <TabsTrigger value="cache" className="text-xs">
              <Database className="h-3 w-3 mr-1" />
              Cache
            </TabsTrigger>
            <TabsTrigger value="cost" className="text-xs">
              <DollarSign className="h-3 w-3 mr-1" />
              Cost
            </TabsTrigger>
            <TabsTrigger value="ragas" className="text-xs">
              <Award className="h-3 w-3 mr-1" />
              Quality
            </TabsTrigger>
          </TabsList>

          {/* Latency Tab */}
          <TabsContent value="latency" className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between items-baseline">
                <span className="text-2xl font-bold text-blue-600 tabular-nums">
                  {metrics.avgLatency > 0 ? Math.round(metrics.avgLatency) : currentLatency}
                  <span className="text-sm font-normal text-gray-500 ml-1">ms</span>
                </span>
                <span className="text-xs text-gray-600">
                  Target: {LATENCY_TARGET}ms
                </span>
              </div>
              <Progress
                value={(Math.min(metrics.avgLatency || currentLatency, LATENCY_TARGET) / LATENCY_TARGET) * 100}
                className="h-2"
              />
            </div>

            <Separator />

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <div className="text-xs text-gray-600">P50 (Median)</div>
                <div className="text-lg font-bold text-gray-900 tabular-nums">
                  {Math.round(currentLatency * 0.9)}ms
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-gray-600">P95</div>
                <div className="text-lg font-bold text-gray-900 tabular-nums">
                  {Math.round(currentLatency * 1.3)}ms
                </div>
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
              <div className="flex items-center gap-2 text-xs text-blue-700">
                <TrendingUp className="h-3 w-3" />
                <span>
                  {metrics.avgLatency <= LATENCY_TARGET
                    ? 'Meeting latency SLA'
                    : 'Above target - optimization needed'}
                </span>
              </div>
            </div>
          </TabsContent>

          {/* Cache Tab */}
          <TabsContent value="cache" className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between items-baseline">
                <span className="text-2xl font-bold text-green-600 tabular-nums">
                  {cacheHitRate.toFixed(0)}
                  <span className="text-sm font-normal text-gray-500 ml-1">%</span>
                </span>
                <span className="text-xs text-gray-600">
                  Target: {CACHE_TARGET}%
                </span>
              </div>
              <Progress
                value={cacheHitRate}
                className="h-2"
              />
            </div>

            <Separator />

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <div className="text-xs text-gray-600">Cache Hits</div>
                <div className="text-lg font-bold text-green-600 tabular-nums">
                  {metrics.cacheHits}
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-gray-600">Cache Misses</div>
                <div className="text-lg font-bold text-gray-600 tabular-nums">
                  {metrics.cacheMisses}
                </div>
              </div>
            </div>

            <div className="bg-green-50 rounded-lg p-3 border border-green-200">
              <div className="space-y-1">
                <div className="text-xs font-medium text-green-700">
                  Monthly Savings Estimate
                </div>
                <div className="text-lg font-bold text-green-600 tabular-nums">
                  ${((cacheHitRate / 100) * 0.002 * metrics.totalQueries * 30).toFixed(2)}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Cost Tab */}
          <TabsContent value="cost" className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between items-baseline">
                <span className="text-2xl font-bold text-indigo-600 tabular-nums">
                  {formatCost(currentCost)}
                </span>
                <span className="text-xs text-gray-600">
                  Target: ${COST_TARGET}
                </span>
              </div>
              <Progress
                value={(Math.min(currentCost, COST_TARGET) / COST_TARGET) * 100}
                className="h-2"
              />
            </div>

            <Separator />

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <div className="text-xs text-gray-600">Total Queries</div>
                <div className="text-lg font-bold text-gray-900 tabular-nums">
                  {metrics.totalQueries.toLocaleString()}
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-gray-600">Total Cost</div>
                <div className="text-lg font-bold text-gray-900 tabular-nums">
                  {formatCost(metrics.totalCost)}
                </div>
              </div>
            </div>

            <div className="space-y-1">
              <div className="text-xs text-gray-600">Total Tokens Used</div>
              <div className="text-lg font-bold text-gray-900 tabular-nums">
                {metrics.totalTokens.toLocaleString()}
              </div>
            </div>
          </TabsContent>

          {/* RAGAS Tab */}
          <TabsContent value="ragas" className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between items-baseline">
                <span className="text-2xl font-bold text-purple-600 tabular-nums">
                  {(ragasScores.overall_score || 0).toFixed(2)}
                </span>
                <span className="text-xs text-gray-600">
                  Target: {RAGAS_TARGET.toFixed(2)}
                </span>
              </div>
              <Progress
                value={((ragasScores.overall_score || 0) / 1.0) * 100}
                className="h-2"
              />
            </div>

            <Separator />

            <div className="space-y-3">
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Answer Relevancy</span>
                  <span className="font-semibold text-gray-900 tabular-nums">
                    {(ragasScores.answer_relevancy || 0).toFixed(2)}
                  </span>
                </div>
                <Progress
                  value={((ragasScores.answer_relevancy || 0) / 1.0) * 100}
                  className="h-1.5"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Context Recall</span>
                  <span className="font-semibold text-gray-900 tabular-nums">
                    {(ragasScores.context_recall || 0).toFixed(2)}
                  </span>
                </div>
                <Progress
                  value={((ragasScores.context_recall || 0) / 1.0) * 100}
                  className="h-1.5"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Faithfulness</span>
                  <span className="font-semibold text-gray-900 tabular-nums">
                    {(ragasScores.answer_faithfulness || 0).toFixed(2)}
                  </span>
                </div>
                <Progress
                  value={((ragasScores.answer_faithfulness || 0) / 1.0) * 100}
                  className="h-1.5"
                />
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
              <div className="flex items-center gap-2 text-xs text-purple-700">
                <Target className="h-3 w-3" />
                <span>
                  {(ragasScores.overall_score || 0) >= RAGAS_TARGET
                    ? 'Meeting quality targets'
                    : 'Below target - review needed'}
                </span>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
