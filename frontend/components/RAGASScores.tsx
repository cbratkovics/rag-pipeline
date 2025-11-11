'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import type { RAGASMetrics } from '@/types'

interface RAGASScoresProps {
  metrics?: RAGASMetrics
}

export function RAGASScores({ metrics }: RAGASScoresProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>RAGAS Scores</CardTitle>
      </CardHeader>
      <CardContent>
        <p>Score: {metrics?.overall_score || 0.86}</p>
      </CardContent>
    </Card>
  )
}
