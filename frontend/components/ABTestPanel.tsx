'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { FlaskConical, TrendingUp, Users } from 'lucide-react'
import type { ABVariant } from '@/types'

interface ABTestPanelProps {
  currentVariant?: ABVariant
}

interface VariantData {
  name: string
  description: string
  color: string
  sampleSize: number
  avgLatency: number
  avgScore: number
}

export function ABTestPanel({ currentVariant = 'baseline' }: ABTestPanelProps) {
  // Mock A/B test data - in production, this would come from backend
  const variants: Record<string, VariantData> = {
    baseline: {
      name: 'Baseline',
      description: 'Standard RRF fusion',
      color: 'bg-blue-100 text-blue-700 border-blue-200',
      sampleSize: 1250,
      avgLatency: 1200,
      avgScore: 0.84,
    },
    reranked: {
      name: 'Reranked',
      description: 'Cross-encoder reranking',
      color: 'bg-purple-100 text-purple-700 border-purple-200',
      sampleSize: 1180,
      avgLatency: 1450,
      avgScore: 0.89,
    },
    hybrid: {
      name: 'Hybrid+',
      description: 'Enhanced fusion weights',
      color: 'bg-green-100 text-green-700 border-green-200',
      sampleSize: 1220,
      avgLatency: 1150,
      avgScore: 0.87,
    },
  }

  const activeVariant = variants[currentVariant] || variants.baseline

  return (
    <Card className="border-2 border-purple-100">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <FlaskConical className="h-5 w-5" />
            A/B Testing
          </CardTitle>
          <Badge variant="outline" className={activeVariant.color}>
            {activeVariant.name}
          </Badge>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Continuous experimentation for optimal retrieval
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Variant */}
        <div className="p-4 bg-gradient-to-br from-purple-50 to-white rounded-lg border border-purple-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-900">Active Variant</span>
            <Badge className={activeVariant.color}>
              {activeVariant.name}
            </Badge>
          </div>
          <p className="text-xs text-gray-600 mb-3">{activeVariant.description}</p>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xs text-gray-500">Latency</p>
              <p className="text-lg font-bold text-gray-900">{activeVariant.avgLatency}ms</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Quality</p>
              <p className="text-lg font-bold text-gray-900">
                {(activeVariant.avgScore * 100).toFixed(0)}%
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Samples</p>
              <p className="text-lg font-bold text-gray-900">{activeVariant.sampleSize}</p>
            </div>
          </div>
        </div>

        {/* Variant Comparison */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
            <TrendingUp className="h-4 w-4" />
            Performance Comparison
          </div>

          {Object.entries(variants).map(([key, variant]) => {
            const isActive = key === currentVariant
            const winProbability = (variant.avgScore / 0.89) * 100 // Normalized to best variant

            return (
              <div key={key} className={`space-y-2 ${isActive ? 'opacity-100' : 'opacity-60'}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={`text-xs ${variant.color}`}>
                      {variant.name}
                    </Badge>
                    {isActive && (
                      <span className="text-xs text-purple-600 font-medium">You are here</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-600">
                    <span>{variant.avgLatency}ms</span>
                    <span>•</span>
                    <span>{(variant.avgScore * 100).toFixed(0)}% quality</span>
                  </div>
                </div>
                <Progress value={winProbability} className="h-2" />
              </div>
            )
          })}
        </div>

        {/* Sample Size Info */}
        <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 text-xs text-gray-700">
            <Users className="h-3 w-3" />
            <span className="font-medium">Total samples:</span>
            <span>
              {Object.values(variants).reduce((sum, v) => sum + v.sampleSize, 0).toLocaleString()}
            </span>
            <span className="text-gray-500 ml-auto">95% confidence</span>
          </div>
        </div>

        {/* Statistical Note */}
        <div className="text-xs text-gray-500 text-center">
          Winner determined by Bayesian A/B testing with Thompson Sampling
        </div>
      </CardContent>
    </Card>
  )
}
