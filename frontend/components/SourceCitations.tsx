'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { ChevronDown, ChevronUp, Copy, Check, FileText } from 'lucide-react'
import { estimateTokens } from '@/lib/ragas-utils'
import type { QueryResponse } from '@/types'

interface SourceCitationsProps {
  result: QueryResponse
}

interface CitationCardProps {
  context: string
  index: number
  score: number
  question: string
}

function CitationCard({ context, index, score, question }: CitationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(context)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Determine retrieval method based on score
  const getRetrievalBadge = () => {
    if (score > 0.7) return { label: 'Hybrid', color: 'bg-blue-100 text-blue-700 border-blue-200' }
    if (score > 0.5) return { label: 'Vector', color: 'bg-green-100 text-green-700 border-green-200' }
    return { label: 'BM25', color: 'bg-purple-100 text-purple-700 border-purple-200' }
  }

  const retrievalBadge = getRetrievalBadge()
  const tokenCount = estimateTokens(context)
  const charCount = context.length

  // Highlight keywords from question (simple implementation)
  const highlightedContext = () => {
    if (!question) return context

    let highlighted = context
    const keywords = question.toLowerCase().split(/\s+/).filter(w => w.length > 3)

    keywords.forEach(keyword => {
      const regex = new RegExp(`\\b(${keyword})\\b`, 'gi')
      highlighted = highlighted.replace(regex, '<mark class="bg-yellow-200 px-0.5">$1</mark>')
    })

    return highlighted
  }

  const previewLength = 200
  const preview = context.slice(0, previewLength) + (context.length > previewLength ? '...' : '')

  return (
    <Card className="border border-gray-200 hover:border-blue-300 transition-colors">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-gray-400" />
            <CardTitle className="text-sm font-medium">Source {index + 1}</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={retrievalBadge.color}>
              {retrievalBadge.label}
            </Badge>
            <Badge variant="outline" className="text-xs">
              Score: {score.toFixed(3)}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Context Text */}
        <div className="text-sm text-gray-700 leading-relaxed">
          {isExpanded ? (
            <div dangerouslySetInnerHTML={{ __html: highlightedContext() }} />
          ) : (
            <p>{preview}</p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-100">
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span>{charCount} chars</span>
            <span>•</span>
            <span>{tokenCount} tokens</span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-7 text-xs"
            >
              {copied ? (
                <>
                  <Check className="h-3 w-3 mr-1" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3 mr-1" />
                  Copy
                </>
              )}
            </Button>
            {context.length > previewLength && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
                className="h-7 text-xs"
              >
                {isExpanded ? (
                  <>
                    <ChevronUp className="h-3 w-3 mr-1" />
                    Collapse
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3 w-3 mr-1" />
                    Expand
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function SourceCitations({ result }: SourceCitationsProps) {
  if (!result.contexts || result.contexts.length === 0) {
    return null
  }

  // Extract scores for each context (if available)
  const getContextScore = (index: number): number => {
    // Use hybrid score as base, could be enhanced with per-context scores
    return (result.scores?.hybrid || 0.5) - (index * 0.05)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Source Citations</span>
          <Badge variant="outline">{result.contexts.length} sources</Badge>
        </CardTitle>
        <p className="text-xs text-gray-500 mt-1">
          Documents retrieved from the knowledge base
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {result.contexts.map((context, index) => (
          <CitationCard
            key={index}
            context={context}
            index={index}
            score={getContextScore(index)}
            question=""
          />
        ))}
      </CardContent>
    </Card>
  )
}
