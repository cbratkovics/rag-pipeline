'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'

interface HybridSearchBreakdownProps {
  bm25Count?: number
  vectorCount?: number
  rrfScore?: number
  rrfK?: number
}

export function HybridSearchBreakdown({
  bm25Count = 8,
  vectorCount = 8,
  rrfScore = 0.92,
  rrfK = 60
}: HybridSearchBreakdownProps) {
  const bm25Percentage = (bm25Count / 10) * 100
  const vectorPercentage = (vectorCount / 10) * 100

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="text-sm font-medium">Hybrid Retrieval Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label className="text-xs font-normal">BM25 (Keyword)</Label>
              <span className="text-xs text-gray-500">{bm25Count} docs</span>
            </div>
            <Progress value={bm25Percentage} className="h-2" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label className="text-xs font-normal">Vector (Semantic)</Label>
              <span className="text-xs text-gray-500">{vectorCount} docs</span>
            </div>
            <Progress value={vectorPercentage} className="h-2" />
          </div>
        </div>
        <div className="flex justify-between items-center pt-2 border-t">
          <span className="text-xs text-gray-600">Reciprocal Rank Fusion</span>
          <span className="text-xs font-medium">Score: {rrfScore.toFixed(2)} (k={rrfK})</span>
        </div>
      </CardContent>
    </Card>
  )
}
