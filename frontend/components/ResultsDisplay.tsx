'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import type { QueryResponse } from '@/types'

interface ResultsDisplayProps {
  result: QueryResponse
}

export function ResultsDisplay({ result }: ResultsDisplayProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Answer</CardTitle>
      </CardHeader>
      <CardContent>
        <p>{result?.answer || 'No answer available'}</p>
      </CardContent>
    </Card>
  )
}
