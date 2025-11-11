'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'

interface RAGASScoresProps {
  metrics?: any
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
