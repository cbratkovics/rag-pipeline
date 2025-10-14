'use client'

import { useState } from 'react'
import { Copy, Check, ExternalLink } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { copyToClipboard, truncate } from '@/lib/utils'
import type { QueryResponse } from '@/types'

interface SourceCitationsProps {
  result: QueryResponse
}

export function SourceCitations({ result }: SourceCitationsProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

  const handleCopy = async (text: string, index: number) => {
    const success = await copyToClipboard(text)
    if (success) {
      setCopiedIndex(index)
      setTimeout(() => setCopiedIndex(null), 2000)
    }
  }

  // Extract metadata if available, otherwise create basic metadata
  const sources = result.contexts.map((context, index) => {
    const metadata = result.metadata?.[index] || {}

    return {
      id: metadata.id || `source-${index + 1}`,
      title: metadata.title || `Source ${index + 1}`,
      content: context,
      snippet: truncate(context, 200),
      source: metadata.source || 'Unknown',
      relevance_score: metadata.relevance_score !== undefined
        ? metadata.relevance_score
        : result.scores.hybrid || 0,
      retrieval_method: metadata.retrieval_method || 'hybrid',
    }
  })

  const getRetrievalBadgeColor = (method: string): "default" | "secondary" | "outline" => {
    switch (method) {
      case 'bm25':
        return 'secondary'
      case 'vector':
        return 'default'
      case 'hybrid':
      default:
        return 'outline'
    }
  }

  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-amber-600'
    return 'text-gray-600'
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Source Citations</CardTitle>
            <CardDescription>
              {sources.length} document{sources.length !== 1 ? 's' : ''} retrieved
            </CardDescription>
          </div>
          <Badge variant="secondary">
            {Object.keys(result.scores).join(' + ')}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <Accordion type="single" collapsible className="w-full">
          {sources.map((source, index) => (
            <AccordionItem key={source.id} value={`item-${index}`}>
              <AccordionTrigger className="hover:no-underline">
                <div className="flex items-center justify-between w-full pr-4">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-600 text-xs font-semibold">
                      {index + 1}
                    </span>
                    <span className="font-medium text-left">{source.title}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant={getRetrievalBadgeColor(source.retrieval_method)}>
                      {source.retrieval_method}
                    </Badge>
                    <span className={`text-sm font-semibold ${getScoreColor(source.relevance_score)}`}>
                      {source.relevance_score.toFixed(2)}
                    </span>
                  </div>
                </div>
              </AccordionTrigger>

              <AccordionContent>
                <div className="space-y-4 pt-2">
                  {/* Source metadata */}
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <ExternalLink className="h-3 w-3" />
                      {source.source}
                    </span>
                    <span>•</span>
                    <span>ID: {source.id}</span>
                  </div>

                  {/* Content */}
                  <div className="p-4 bg-gray-50 rounded-md border border-gray-200">
                    <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                      {source.content}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCopy(source.content, index)}
                      className="gap-2"
                    >
                      {copiedIndex === index ? (
                        <>
                          <Check className="h-3 w-3" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-3 w-3" />
                          Copy
                        </>
                      )}
                    </Button>

                    <span className="text-xs text-gray-500">
                      {source.content.length} characters
                    </span>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>

        {/* Score legend */}
        <div className="mt-6 p-4 bg-gray-50 rounded-md border border-gray-200">
          <p className="text-xs font-medium text-gray-700 mb-2">Retrieval Methods:</p>
          <div className="flex flex-wrap gap-2 text-xs">
            <div className="flex items-center gap-1">
              <Badge variant="secondary">BM25</Badge>
              <span className="text-gray-600">Keyword matching</span>
            </div>
            <div className="flex items-center gap-1">
              <Badge variant="default">Vector</Badge>
              <span className="text-gray-600">Semantic similarity</span>
            </div>
            <div className="flex items-center gap-1">
              <Badge variant="outline">Hybrid</Badge>
              <span className="text-gray-600">Combined (RRF)</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
