'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'

interface ResultsDisplayProps {
  result: any
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
