'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'

interface MetricsPanelProps {
  result?: any
  provider?: string
}

export function MetricsPanel({ result, provider }: MetricsPanelProps) {
  return (
    <div className="grid grid-cols-4 gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Latency</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{result?.latency_ms || 0}ms</p>
        </CardContent>
      </Card>
    </div>
  )
}
