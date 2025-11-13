'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Crown, TrendingUp, Zap, DollarSign, Award } from 'lucide-react'
import type { ABVariant } from '@/types'

interface ABVariantData {
  variant: ABVariant
  name: string
  description: string
  trafficAllocation: number
  metrics: {
    avgLatency: number
    ragasScore: number
    costPerQuery: number
    queries: number
  }
  isChampion?: boolean
  winProbability?: number
}

interface ABDeckProps {
  variants?: ABVariantData[]
  showWinProbability?: boolean
}

const defaultVariants: ABVariantData[] = [
  {
    variant: 'baseline',
    name: 'Baseline',
    description: 'Standard RRF fusion',
    trafficAllocation: 50,
    metrics: {
      avgLatency: 485,
      ragasScore: 0.87,
      costPerQuery: 0.0021,
      queries: 12450,
    },
    isChampion: false,
    winProbability: 32,
  },
  {
    variant: 'reranked',
    name: 'Reranked',
    description: 'Cross-encoder reranking',
    trafficAllocation: 30,
    metrics: {
      avgLatency: 520,
      ragasScore: 0.91,
      costPerQuery: 0.0024,
      queries: 7470,
    },
    isChampion: true,
    winProbability: 68,
  },
  {
    variant: 'hybrid',
    name: 'Hybrid+',
    description: 'Weighted fusion experiment',
    trafficAllocation: 20,
    metrics: {
      avgLatency: 450,
      ragasScore: 0.89,
      costPerQuery: 0.0019,
      queries: 4980,
    },
    isChampion: false,
    winProbability: 45,
  },
]

export function ABDeck({ variants = defaultVariants, showWinProbability = true }: ABDeckProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">A/B Test Variants</h3>
        <Badge variant="outline" className="text-blue-600 border-blue-200 bg-blue-50">
          {variants.length} Active
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {variants.map((variant) => (
          <Card
            key={variant.variant}
            className={`border-2 transition-all hover:shadow-lg ${
              variant.isChampion
                ? 'border-amber-300 bg-gradient-to-br from-amber-50 to-yellow-50'
                : 'border-gray-200'
            }`}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-base font-bold">
                      {variant.name}
                    </CardTitle>
                    {variant.isChampion && (
                      <Badge className="bg-amber-500 text-white border-0 shadow-sm">
                        <Crown className="h-3 w-3 mr-1" />
                        Champion
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-gray-600">{variant.description}</p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Traffic Allocation */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Traffic Allocation</span>
                  <span className="font-semibold text-gray-900">
                    {variant.trafficAllocation}%
                  </span>
                </div>
                <Progress value={variant.trafficAllocation} className="h-2" />
              </div>

              {/* Win Probability */}
              {showWinProbability && variant.winProbability !== undefined && (
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-600 flex items-center gap-1">
                      <Award className="h-3 w-3" />
                      Win Probability
                    </span>
                    <span className="text-sm font-bold text-blue-600">
                      {variant.winProbability}%
                    </span>
                  </div>
                  <Progress
                    value={variant.winProbability}
                    className="h-1.5"
                  />
                </div>
              )}

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-white rounded-md p-2 border border-gray-200">
                  <div className="flex items-center gap-1 mb-1">
                    <Zap className="h-3 w-3 text-blue-500" />
                    <span className="text-xs text-gray-600">Latency</span>
                  </div>
                  <p className="text-sm font-bold text-gray-900 tabular-nums">
                    {variant.metrics.avgLatency}ms
                  </p>
                </div>

                <div className="bg-white rounded-md p-2 border border-gray-200">
                  <div className="flex items-center gap-1 mb-1">
                    <TrendingUp className="h-3 w-3 text-purple-500" />
                    <span className="text-xs text-gray-600">RAGAS</span>
                  </div>
                  <p className="text-sm font-bold text-gray-900 tabular-nums">
                    {variant.metrics.ragasScore.toFixed(2)}
                  </p>
                </div>

                <div className="bg-white rounded-md p-2 border border-gray-200">
                  <div className="flex items-center gap-1 mb-1">
                    <DollarSign className="h-3 w-3 text-green-500" />
                    <span className="text-xs text-gray-600">Cost</span>
                  </div>
                  <p className="text-sm font-bold text-gray-900 tabular-nums">
                    ${variant.metrics.costPerQuery.toFixed(4)}
                  </p>
                </div>

                <div className="bg-white rounded-md p-2 border border-gray-200">
                  <div className="flex items-center gap-1 mb-1">
                    <span className="text-xs text-gray-600">Queries</span>
                  </div>
                  <p className="text-sm font-bold text-gray-900 tabular-nums">
                    {variant.metrics.queries.toLocaleString()}
                  </p>
                </div>
              </div>

              {/* Comparison to Champion */}
              {!variant.isChampion && showWinProbability && (
                <div className="pt-2 border-t border-gray-200">
                  <p className="text-xs text-gray-500 text-center">
                    {variant.winProbability && variant.winProbability > 50
                      ? '🚀 Leading candidate for promotion'
                      : '📊 Collecting more data...'}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <TrendingUp className="h-5 w-5 text-blue-600" />
          </div>
          <div className="flex-1 space-y-1">
            <h4 className="text-sm font-semibold text-blue-900">
              Bayesian A/B Testing
            </h4>
            <p className="text-xs text-blue-700">
              Win probabilities calculated using Bayesian inference with Beta priors.
              Champion is promoted when P(better) &gt; 95%.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
