'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Calculator, TrendingUp } from 'lucide-react'

export function ROIInline() {
  const [qps, setQps] = useState(10)
  const [costPerQuery, setCostPerQuery] = useState(0.002)
  const [cacheHitRate, setCacheHitRate] = useState(85)

  // Calculate monthly savings
  const queriesPerMonth = qps * 60 * 60 * 24 * 30
  const totalCostWithoutCache = queriesPerMonth * costPerQuery
  const cachedQueries = queriesPerMonth * (cacheHitRate / 100)
  const cacheQueryCost = 0.0001 // Assume cache queries cost 95% less
  const cacheSavings = cachedQueries * (costPerQuery - cacheQueryCost)
  const totalCostWithCache = totalCostWithoutCache - cacheSavings
  const savingsPercentage = ((cacheSavings / totalCostWithoutCache) * 100)

  const formatCurrency = (value: number) => {
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(2)}K`
    }
    return `$${value.toFixed(2)}`
  }

  const formatNumber = (value: number) => {
    return value.toLocaleString()
  }

  return (
    <Card className="border-2">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Calculator className="h-4 w-4 text-blue-600" />
            ROI Calculator
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Inputs */}
        <div className="grid grid-cols-3 gap-3">
          <div className="space-y-1">
            <Label htmlFor="qps" className="text-xs text-gray-600">
              QPS
            </Label>
            <Input
              id="qps"
              type="number"
              value={qps}
              onChange={(e) => setQps(Number(e.target.value))}
              min={1}
              max={1000}
              className="h-8 text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="cost" className="text-xs text-gray-600">
              Cost/Query
            </Label>
            <Input
              id="cost"
              type="number"
              value={costPerQuery}
              onChange={(e) => setCostPerQuery(Number(e.target.value))}
              step={0.0001}
              min={0}
              max={1}
              className="h-8 text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="cache" className="text-xs text-gray-600">
              Cache %
            </Label>
            <Input
              id="cache"
              type="number"
              value={cacheHitRate}
              onChange={(e) => setCacheHitRate(Number(e.target.value))}
              min={0}
              max={100}
              className="h-8 text-sm"
            />
          </div>
        </div>

        {/* Results */}
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-600">Monthly Queries</span>
              <span className="text-sm font-semibold text-gray-900 tabular-nums">
                {formatNumber(queriesPerMonth)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-600">Cost w/o Cache</span>
              <span className="text-sm font-semibold text-gray-900 tabular-nums">
                {formatCurrency(totalCostWithoutCache)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-600">Cost w/ Cache</span>
              <span className="text-sm font-semibold text-gray-900 tabular-nums">
                {formatCurrency(totalCostWithCache)}
              </span>
            </div>
            <div className="pt-2 border-t border-green-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-green-700 flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  Monthly Savings
                </span>
                <span className="text-lg font-bold text-green-600 tabular-nums">
                  {formatCurrency(cacheSavings)}
                </span>
              </div>
              <div className="flex justify-end mt-1">
                <span className="text-xs text-green-600 font-medium">
                  ({savingsPercentage.toFixed(1)}% reduction)
                </span>
              </div>
            </div>
          </div>
        </div>

        <p className="text-xs text-gray-500 text-center">
          Assuming 95% cost reduction per cached query
        </p>
      </CardContent>
    </Card>
  )
}
