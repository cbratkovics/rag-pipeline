/**
 * Utility functions for calculating RAGAS-inspired metrics from query results
 * These are approximations based on available data, not actual RAGAS library calculations
 */

import type { QueryResponse, RAGASMetrics } from '@/types'

/**
 * Calculate Context Relevancy based on hybrid scores
 * Higher hybrid scores indicate more relevant contexts
 */
export function calculateContextRelevancy(result: QueryResponse): number {
  const hybridScore = result.scores?.hybrid || 0
  // Normalize to 0-1 range (assuming hybrid scores are typically 0-10)
  return Math.min(hybridScore / 10, 1)
}

/**
 * Calculate Answer Faithfulness by checking if answer references contexts
 * Measures if the answer is grounded in the retrieved contexts
 */
export function calculateAnswerFaithfulness(result: QueryResponse): number {
  if (!result.answer || !result.contexts || result.contexts.length === 0) {
    return 0
  }

  const answer = result.answer.toLowerCase()
  const contexts = result.contexts.map(c => c.toLowerCase())

  // Count how many significant words from the answer appear in contexts
  const answerWords = answer
    .split(/\s+/)
    .filter(word => word.length > 4) // Only significant words
    .slice(0, 20) // Sample first 20 words

  if (answerWords.length === 0) return 0.5

  let matchedWords = 0
  answerWords.forEach(word => {
    if (contexts.some(context => context.includes(word))) {
      matchedWords++
    }
  })

  return matchedWords / answerWords.length
}

/**
 * Calculate Answer Relevancy based on answer quality indicators
 * Considers answer length, completeness, and structure
 */
export function calculateAnswerRelevancy(result: QueryResponse, question: string): number {
  if (!result.answer || !question) return 0

  const answer = result.answer
  const answerLength = answer.length

  // Factors for relevancy
  let score = 0.5 // Base score

  // Length factor (optimal range: 100-500 chars)
  if (answerLength >= 100 && answerLength <= 500) {
    score += 0.2
  } else if (answerLength > 50) {
    score += 0.1
  }

  // Check if answer contains question keywords
  const questionWords = question.toLowerCase().split(/\s+/).filter(w => w.length > 3)
  const answerLower = answer.toLowerCase()
  const keywordMatches = questionWords.filter(word => answerLower.includes(word)).length
  score += Math.min((keywordMatches / questionWords.length) * 0.3, 0.3)

  return Math.min(score, 1)
}

/**
 * Calculate Context Recall based on number and quality of contexts
 * Measures if all relevant information was retrieved
 */
export function calculateContextRecall(result: QueryResponse): number {
  if (!result.contexts || result.contexts.length === 0) return 0

  const numContexts = result.contexts.length
  const avgContextLength = result.contexts.reduce((sum, c) => sum + c.length, 0) / numContexts

  // Base score from number of contexts (more contexts = better recall)
  let score = Math.min(numContexts / 4, 0.7) // Max 0.7 from count

  // Bonus for substantial contexts (>100 chars each)
  if (avgContextLength > 100) {
    score += 0.3
  } else if (avgContextLength > 50) {
    score += 0.15
  }

  return Math.min(score, 1)
}

/**
 * Calculate overall RAGAS metrics for a query result
 */
export function calculateRAGASMetrics(
  result: QueryResponse,
  question: string = ''
): RAGASMetrics {
  const contextRelevancy = calculateContextRelevancy(result)
  const answerFaithfulness = calculateAnswerFaithfulness(result)
  const answerRelevancy = calculateAnswerRelevancy(result, question)
  const contextRecall = calculateContextRecall(result)

  const overallScore = (
    contextRelevancy +
    answerFaithfulness +
    answerRelevancy +
    contextRecall
  ) / 4

  return {
    context_relevancy: contextRelevancy,
    answer_faithfulness: answerFaithfulness,
    answer_relevancy: answerRelevancy,
    context_recall: contextRecall,
    overall_score: overallScore,
  }
}

/**
 * Get color coding based on score
 */
export function getScoreColor(score: number): string {
  if (score >= 0.8) return 'text-green-600'
  if (score >= 0.6) return 'text-yellow-600'
  return 'text-red-600'
}

/**
 * Get background color for score badges
 */
export function getScoreBgColor(score: number): string {
  if (score >= 0.8) return 'bg-green-50 border-green-200'
  if (score >= 0.6) return 'bg-yellow-50 border-yellow-200'
  return 'bg-red-50 border-red-200'
}

/**
 * Format score as percentage
 */
export function formatScore(score: number): string {
  return `${(score * 100).toFixed(0)}%`
}

/**
 * Estimate token count from text
 * Rough approximation: ~4 characters per token
 */
export function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4)
}

/**
 * Calculate cost based on tokens and provider
 */
export function calculateCost(tokens: number, provider: 'stub' | 'openai'): number {
  const pricePerToken = provider === 'openai' ? 0.002 / 1000 : 0.0015 / 1000
  return tokens * pricePerToken
}

/**
 * Format cost in USD
 */
export function formatCost(cost: number): string {
  if (cost < 0.01) {
    return `$${(cost * 1000).toFixed(3)}m` // Show in thousandths
  }
  return `$${cost.toFixed(4)}`
}

/**
 * Get latency color coding
 */
export function getLatencyColor(latencyMs: number): string {
  if (latencyMs < 1000) return 'text-green-600'
  if (latencyMs < 2000) return 'text-yellow-600'
  return 'text-red-600'
}

/**
 * Get latency background color
 */
export function getLatencyBgColor(latencyMs: number): string {
  if (latencyMs < 1000) return 'bg-green-50 border-green-200'
  if (latencyMs < 2000) return 'bg-yellow-50 border-yellow-200'
  return 'bg-red-50 border-red-200'
}

/**
 * Calculate cache hit rate percentage
 */
export function calculateCacheHitRate(hits: number, misses: number): number {
  const total = hits + misses
  if (total === 0) return 0
  return (hits / total) * 100
}

/**
 * Calculate error rate percentage
 */
export function calculateErrorRate(errors: number, total: number): number {
  if (total === 0) return 0
  return (errors / total) * 100
}
