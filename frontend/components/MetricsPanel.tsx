'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock } from 'lucide-react'
import { DollarSign } from 'lucide-react'
import { FileText } from 'lucide-react'
import { Zap } from 'lucide-react'
import type { QueryResponse } from '@/types'
import { estimateOpenAICost } from '@/lib/api'
import { formatDuration, formatCost, formatNumber } from '@/lib/utils'

interface MetricsPanelProps {
  result: QueryResponse
  provider: 'stub' | 'openai'
}

export function MetricsPanel({ result, provider }: MetricsPanelProps) {
  // Estimate token count (rough approximation: 1 token ≈ 4 characters)
  const estimatedTokens = Math.ceil(
    (result.answer.length + result.contexts.join('').length) / 4
  )

  // Estimate cost for OpenAI
  const estimatedCost = provider === 'openai'
    ? estimateOpenAICost(estimatedTokens, 'gpt-3.5-turbo')
    : 0

  const metrics = [
    {
      icon: Clock,
      label: 'Latency',
      value: formatDuration(result.latency_ms),
      description: 'Total processing time',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      icon: FileText,
      label: 'Contexts',
      value: result.contexts.length.toString(),
      description: 'Retrieved documents',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      icon: Zap,
      label: 'Tokens',
      value: formatNumber(estimatedTokens),
      description: 'Estimated token count',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      icon: DollarSign,
      label: 'Cost',
      value: provider === 'openai' ? formatCost(estimatedCost) : 'Free',
      description: provider === 'openai' ? 'Estimated API cost' : 'Stub provider',
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric) => (
        <Card key={metric.label} className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2 flex-1">
                <p className="text-sm font-medium text-gray-500">{metric.label}</p>
                <p className="text-2xl font-bold">{metric.value}</p>
                <p className="text-xs text-gray-400">{metric.description}</p>
              </div>
              <div className={`rounded-full p-2 ${metric.bgColor}`}>
                <metric.icon className={`h-5 w-5 ${metric.color}`} />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
