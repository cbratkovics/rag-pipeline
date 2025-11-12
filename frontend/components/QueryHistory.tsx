'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { History, Trash2, RotateCcw, Download } from 'lucide-react'
import { useMetrics } from '@/contexts/MetricsContext'
import { formatDistanceToNow } from '@/lib/date-utils'

interface QueryHistoryProps {
  onRerun?: (question: string) => void
}

export function QueryHistory({ onRerun }: QueryHistoryProps) {
  const { getQueryHistory, clearMetrics } = useMetrics()
  const history = getQueryHistory()

  const handleExport = () => {
    const dataStr = JSON.stringify(history, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `rag-query-history-${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  if (history.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Query History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500 text-center py-8">
            No queries yet. Run a search to see history.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Query History
            <Badge variant="outline">{history.length}</Badge>
          </CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="h-3 w-3 mr-1" />
              Export
            </Button>
            <Button variant="outline" size="sm" onClick={clearMetrics}>
              <Trash2 className="h-3 w-3 mr-1" />
              Clear
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 max-h-96 overflow-y-auto">
        {history.slice().reverse().map((item) => (
          <div
            key={item.id}
            className="p-3 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
          >
            <div className="flex items-start justify-between mb-2">
              <p className="text-sm font-medium text-gray-900 line-clamp-2 flex-1">
                {item.question}
              </p>
              {onRerun && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onRerun(item.question)}
                  className="h-6 ml-2"
                >
                  <RotateCcw className="h-3 w-3" />
                </Button>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span>{item.result.latency_ms.toFixed(0)}ms</span>
              <span>•</span>
              <span>{formatDistanceToNow(new Date(item.timestamp))}</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
