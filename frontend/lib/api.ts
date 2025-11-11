// frontend/lib/api.ts

import type { QueryRequest, QueryResponse } from '@/types'

// API Base URL configuration with comprehensive fallback
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000"

// Log configuration for debugging (only in development)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  console.log('[API Config]', {
    API_BASE_URL,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  })
}

// Custom error class for API errors
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

// Retry configuration
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // ms
const RETRY_BACKOFF = 2 // exponential backoff multiplier

// Delay helper
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// Main RAG query function with retry logic
export async function queryRAG(params: QueryRequest, retries = MAX_RETRIES): Promise<QueryResponse> {
  let lastError: Error | null = null

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      console.log(`[queryRAG] Attempt ${attempt + 1}/${retries + 1}`, {
        url: `${API_BASE_URL}/api/v1/query`,
        params
      })

      const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        mode: 'cors',
        credentials: 'omit',
        body: JSON.stringify(params),
      })

      console.log(`[queryRAG] Response:`, {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        headers: Object.fromEntries(response.headers.entries()),
      })

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error')
        const error = new RAGAPIError(
          `Query failed: ${errorText}`,
          response.status,
          'QUERY_ERROR',
          { attempt: attempt + 1, maxRetries: retries + 1 }
        )

        // Retry on 5xx errors
        if (response.status >= 500 && attempt < retries) {
          lastError = error
          const waitTime = RETRY_DELAY * Math.pow(RETRY_BACKOFF, attempt)
          console.log(`[queryRAG] Retrying after ${waitTime}ms due to ${response.status}`)
          await delay(waitTime)
          continue
        }

        throw error
      }

      const data = await response.json()
      console.log(`[queryRAG] Success:`, {
        hasAnswer: !!data.answer,
        contextCount: data.contexts?.length || 0,
      })
      return data
    } catch (error) {
      lastError = error as Error
      console.error(`[queryRAG] Attempt ${attempt + 1} failed:`, error)

      if (error instanceof RAGAPIError) {
        // Don't retry on client errors (4xx)
        if (error.status && error.status >= 400 && error.status < 500) {
          throw error
        }
      }

      // Retry on network errors
      if (attempt < retries) {
        const waitTime = RETRY_DELAY * Math.pow(RETRY_BACKOFF, attempt)
        console.log(`[queryRAG] Retrying after ${waitTime}ms`)
        await delay(waitTime)
        continue
      }
    }
  }

  // All retries exhausted
  throw new RAGAPIError(
    lastError?.message || 'All retry attempts failed',
    undefined,
    'NETWORK_ERROR',
    { attempts: retries + 1 }
  )
}

// Health check function with detailed logging
export async function checkHealth(): Promise<boolean> {
  try {
    // Try multiple endpoints for compatibility
    const endpoints = ['/health', '/healthz', '/api/health', '/health/live']

    console.log('[checkHealth] Testing endpoints:', endpoints)

    for (const endpoint of endpoints) {
      try {
        const url = `${API_BASE_URL}${endpoint}`
        console.log(`[checkHealth] Trying: ${url}`)

        const response = await fetch(url, {
          method: 'GET',
          mode: 'cors',
          credentials: 'omit',
        })

        console.log(`[checkHealth] ${endpoint} response:`, {
          status: response.status,
          ok: response.ok,
        })

        if (response.ok) {
          console.log(`[checkHealth] Success with endpoint: ${endpoint}`)
          return true
        }
      } catch (error) {
        console.log(`[checkHealth] ${endpoint} failed:`, error)
        // Continue to next endpoint
      }
    }

    console.log('[checkHealth] All endpoints failed')
    return false
  } catch (error) {
    console.error('[checkHealth] Unexpected error:', error)
    return false
  }
}

// Generic JSON API function for other endpoints
export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`
  const res = await fetch(url, {
    mode: "cors",
    cache: "no-store",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  })

  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new RAGAPIError(
      `HTTP ${res.status} ${res.statusText} — ${text}`,
      res.status
    )
  }

  return res.json() as Promise<T>
}

// Estimate OpenAI API cost
export function estimateOpenAICost(tokenCount: number, model: string = 'gpt-3.5-turbo'): number {
  const pricing: Record<string, number> = {
    'gpt-3.5-turbo': 0.0015 / 1000,  // $0.0015 per 1K tokens
    'gpt-4': 0.03 / 1000,             // $0.03 per 1K tokens
    'gpt-4-turbo': 0.01 / 1000,       // $0.01 per 1K tokens
  }

  const pricePerToken = pricing[model] || pricing['gpt-3.5-turbo']
  return tokenCount * pricePerToken
}

// Diagnostic types
export interface DiagnosticResult {
  name: string
  status: 'success' | 'error' | 'warning'
  message: string
  details?: Record<string, unknown>
  timestamp: string
}

export interface SystemDiagnostics {
  overall: 'healthy' | 'degraded' | 'down'
  checks: DiagnosticResult[]
  timestamp: string
}

// Comprehensive diagnostics function
export async function runDiagnostics(): Promise<SystemDiagnostics> {
  const checks: DiagnosticResult[] = []
  const timestamp = new Date().toISOString()

  // 1. Check API connectivity
  try {
    const healthOk = await checkHealth()
    checks.push({
      name: 'API Health',
      status: healthOk ? 'success' : 'error',
      message: healthOk ? 'API is reachable' : 'API is not reachable',
      details: { baseUrl: API_BASE_URL },
      timestamp,
    })
  } catch (error) {
    checks.push({
      name: 'API Health',
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error',
      details: { baseUrl: API_BASE_URL },
      timestamp,
    })
  }

  // 2. Check readiness endpoint
  try {
    const response = await fetch(`${API_BASE_URL}/health/ready`, {
      mode: 'cors',
      credentials: 'omit',
    })

    if (response.ok) {
      const data = await response.json()
      checks.push({
        name: 'System Readiness',
        status: data.status === 'ready' ? 'success' : 'warning',
        message: `System is ${data.status}`,
        details: data.checks || {},
        timestamp,
      })
    } else {
      checks.push({
        name: 'System Readiness',
        status: 'warning',
        message: `Readiness check returned ${response.status}`,
        timestamp,
      })
    }
  } catch (error) {
    checks.push({
      name: 'System Readiness',
      status: 'warning',
      message: 'Could not check readiness',
      details: { error: error instanceof Error ? error.message : 'Unknown' },
      timestamp,
    })
  }

  // 3. Test query endpoint
  try {
    const testQuery: QueryRequest = {
      question: 'What is RAG?',
      k: 3,
    }

    const result = await queryRAG(testQuery, 0) // No retries for diagnostic

    // Check if scores are non-zero
    const hasNonZeroScores = (result.scores?.hybrid && result.scores.hybrid > 0) || false

    checks.push({
      name: 'Query Test',
      status: hasNonZeroScores ? 'success' : 'warning',
      message: hasNonZeroScores
        ? 'Query returned non-zero scores'
        : 'Query returned zero scores (vector store may be empty)',
      details: {
        contextCount: result.contexts?.length || 0,
        hasAnswer: !!result.answer,
        sampleScores: result.scores ? [result.scores.hybrid || 0, result.scores.bm25 || 0, result.scores.vector || 0] : [],
      },
      timestamp,
    })
  } catch (error) {
    checks.push({
      name: 'Query Test',
      status: 'error',
      message: error instanceof Error ? error.message : 'Query test failed',
      timestamp,
    })
  }

  // Determine overall status
  const hasErrors = checks.some(c => c.status === 'error')
  const hasWarnings = checks.some(c => c.status === 'warning')

  let overall: 'healthy' | 'degraded' | 'down' = 'healthy'
  if (hasErrors) {
    overall = 'down'
  } else if (hasWarnings) {
    overall = 'degraded'
  }

  return {
    overall,
    checks,
    timestamp,
  }
}
