'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Activity, Database, DollarSign, Zap, TrendingUp, AlertCircle } from 'lucide-react'
import { useMetrics } from '@/contexts/MetricsContext'
import {
  getLatencyColor,
  getLatencyBgColor,
  estimateTokens,
  formatCost,
  calculateCacheHitRate,
  calculateErrorRate
} from '@/lib/ragas-utils'
import type { QueryResponse } from '@/types'

interface MetricsPanelProps {
  result?: QueryResponse
}

export function MetricsPanel({ result }: MetricsPanelProps) {
  const metrics = useMetrics()

  // Calculate current query metrics
  const currentLatency = result ? (result.processing_time_ms || result.latency_ms || 0) : 0

  // Handle both new (sources) and old (contexts) schema
  const contentText = result
    ? result.contexts?.join('') || result.sources?.map(s => s.content || s.snippet || '').join('') || ''
    : '';

  // Use API-provided values or estimate
  const currentTokens = result
    ? (result.token_count || estimateTokens(result.answer + contentText))
    : 0;

  const currentCost = result
    ? (result.cost_usd || currentTokens * (0.002 / 1000))
    : 0;

  // Calculate aggregate metrics
  const cacheHitRate = calculateCacheHitRate(metrics.cacheHits, metrics.cacheMisses)
  const errorRate = calculateErrorRate(metrics.errorCount, metrics.totalQueries)

  // Calculate throughput (queries per minute based on recent activity)
  const recentQueries = metrics.queries.slice(-5)
  let throughput = 0
  if (recentQueries.length > 1) {
    // Simple approximation based on recent query count
    throughput = recentQueries.length * 12 // Rough estimate: queries per minute
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {/* Latency */}
      <Card className={`border-2 ${result ? getLatencyBgColor(currentLatency) : ''}`}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-medium text-gray-600">Latency</CardTitle>
            <Zap className="h-4 w-4 text-gray-400" />
          </div>
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${result ? getLatencyColor(currentLatency) : 'text-gray-900'}`}>
            {currentLatency.toFixed(0)}
            <span className="text-sm font-normal text-gray-500">ms</span>
          </div>
          {metrics.avgLatency > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Avg: {metrics.avgLatency.toFixed(0)}ms
            </p>
          )}
        </CardContent>
      </Card>

      {/* Cache Hit Rate */}
      <Card className={`border-2 ${cacheHitRate > 80 ? 'bg-green-50 border-green-200' : cacheHitRate > 50 ? 'bg-yellow-50 border-yellow-200' : ''}`}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-medium text-gray-600">Cache Hit Rate</CardTitle>
            <Database className="h-4 w-4 text-gray-400" />
          </div>
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${cacheHitRate > 80 ? 'text-green-600' : cacheHitRate > 50 ? 'text-yellow-600' : 'text-gray-900'}`}>
            {cacheHitRate.toFixed(0)}
            <span className="text-sm font-normal text-gray-500">%</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {metrics.cacheHits}/{metrics.cacheHits + metrics.cacheMisses} hits
          </p>
        </CardContent>
      </Card>

      {/* Token Count */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-medium text-gray-600">Tokens</CardTitle>
            <Activity className="h-4 w-4 text-gray-400" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-gray-900">
            {currentTokens > 0 ? currentTokens.toLocaleString() : metrics.totalTokens.toLocaleString()}
          </div>
          {currentTokens > 0 && metrics.totalTokens > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Total: {(metrics.totalTokens / 1000).toFixed(1)}K
            </p>
          )}
        </CardContent>
      </Card>

      {/* Cost */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-medium text-gray-600">Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-gray-400" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-gray-900">
            {currentCost > 0 ? formatCost(currentCost) : formatCost(metrics.totalCost)}
          </div>
          {currentCost > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Total: {formatCost(metrics.totalCost)}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Throughput */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-medium text-gray-600">Throughput</CardTitle>
            <TrendingUp className="h-4 w-4 text-gray-400" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-gray-900">
            {throughput.toFixed(0)}
            <span className="text-sm font-normal text-gray-500">/min</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {metrics.totalQueries} total
          </p>
        </CardContent>
      </Card>

      {/* Error Rate */}
      <Card className={`border-2 ${errorRate > 10 ? 'bg-red-50 border-red-200' : errorRate > 5 ? 'bg-yellow-50 border-yellow-200' : ''}`}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-medium text-gray-600">Error Rate</CardTitle>
            <AlertCircle className="h-4 w-4 text-gray-400" />
          </div>
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${errorRate > 10 ? 'text-red-600' : errorRate > 5 ? 'text-yellow-600' : 'text-gray-900'}`}>
            {errorRate.toFixed(1)}
            <span className="text-sm font-normal text-gray-500">%</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {metrics.errorCount} errors
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
