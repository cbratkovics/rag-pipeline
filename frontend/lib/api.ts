/**
 * API Client for RAG Pipeline Backend
 * Handles all HTTP communication with retry logic and error handling
 */

import type {
  QueryRequest,
  QueryResponse,
  HealthResponse,
  APIError,
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const DEFAULT_TIMEOUT = 30000 // 30 seconds
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 second

/**
 * Custom error class for API errors
 */
export class RAGAPIError extends Error {
  status?: number
  code?: string
  details?: Record<string, unknown>

  constructor(message: string, status?: number, code?: string, details?: Record<string, unknown>) {
    super(message)
    this.name = 'RAGAPIError'
    this.status = status
    this.code = code
    this.details = details
  }
}

/**
 * Sleep utility for retry delays
 */
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * Fetch with timeout
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout: number = DEFAULT_TIMEOUT
): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    })
    clearTimeout(timeoutId)
    return response
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      throw new RAGAPIError('Request timeout', 408, 'TIMEOUT')
    }
    throw error
  }
}

/**
 * Retry wrapper with exponential backoff
 */
async function withRetry<T>(
  operation: () => Promise<T>,
  retries: number = MAX_RETRIES
): Promise<T> {
  let lastError: Error | null = null

  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      return await operation()
    } catch (error) {
      lastError = error as Error

      // Don't retry on client errors (4xx)
      if (error instanceof RAGAPIError && error.status && error.status < 500) {
        throw error
      }

      // Don't retry on last attempt
      if (attempt === retries - 1) {
        break
      }

      // Exponential backoff
      const delay = RETRY_DELAY * Math.pow(2, attempt)
      await sleep(delay)
    }
  }

  throw lastError
}

/**
 * Parse API error response
 */
async function parseError(response: Response): Promise<RAGAPIError> {
  let errorMessage = `API error: ${response.status}`
  let errorDetails: Record<string, unknown> = {}

  try {
    const data = await response.json()
    errorMessage = data.detail || data.message || errorMessage
    errorDetails = data
  } catch {
    // Response is not JSON, use status text
    errorMessage = response.statusText || errorMessage
  }

  return new RAGAPIError(
    errorMessage,
    response.status,
    `HTTP_${response.status}`,
    errorDetails
  )
}

/**
 * Query the RAG pipeline
 */
export async function queryRAG(params: QueryRequest): Promise<QueryResponse> {
  return withRetry(async () => {
    const response = await fetchWithTimeout(
      `${API_URL}/api/v1/query`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      }
    )

    if (!response.ok) {
      throw await parseError(response)
    }

    const data: QueryResponse = await response.json()
    return data
  })
}

/**
 * Check backend health status
 */
export async function checkHealth(): Promise<HealthResponse> {
  try {
    const response = await fetchWithTimeout(
      `${API_URL}/healthz`,
      {
        method: 'GET',
      },
      5000 // Shorter timeout for health check
    )

    if (!response.ok) {
      throw await parseError(response)
    }

    return await response.json()
  } catch (error) {
    // Don't retry health checks
    if (error instanceof RAGAPIError) {
      throw error
    }
    throw new RAGAPIError('Health check failed', 503, 'SERVICE_UNAVAILABLE')
  }
}

/**
 * Get Prometheus metrics (returns raw text)
 */
export async function getMetrics(): Promise<string> {
  const response = await fetchWithTimeout(
    `${API_URL}/metrics`,
    {
      method: 'GET',
    }
  )

  if (!response.ok) {
    throw await parseError(response)
  }

  return await response.text()
}

/**
 * Estimate OpenAI cost based on token count
 * Using GPT-3.5-turbo pricing as reference
 */
export function estimateOpenAICost(
  tokenCount: number,
  model: string = 'gpt-3.5-turbo'
): number {
  const pricing: Record<string, { input: number; output: number }> = {
    'gpt-3.5-turbo': { input: 0.0005 / 1000, output: 0.0015 / 1000 },
    'gpt-4': { input: 0.03 / 1000, output: 0.06 / 1000 },
    'gpt-4-turbo': { input: 0.01 / 1000, output: 0.03 / 1000 },
  }

  const modelPricing = pricing[model] || pricing['gpt-3.5-turbo']
  // Assume 50/50 split between input and output tokens
  const avgCostPerToken = (modelPricing.input + modelPricing.output) / 2
  return tokenCount * avgCostPerToken
}

/**
 * Check if API is available (without throwing)
 */
export async function isAPIAvailable(): Promise<boolean> {
  try {
    await checkHealth()
    return true
  } catch {
    return false
  }
}

/**
 * Format duration in milliseconds to human-readable string
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms.toFixed(0)}ms`
  }
  const seconds = ms / 1000
  if (seconds < 60) {
    return `${seconds.toFixed(2)}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds.toFixed(0)}s`
}

/**
 * Format cost in dollars
 */
export function formatCost(cost: number): string {
  if (cost < 0.01) {
    return `$${(cost * 1000).toFixed(3)}¢`
  }
  return `$${cost.toFixed(4)}`
}

/**
 * Format large numbers with commas
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('en-US')
}
