// frontend/lib/api.ts

import type { QueryRequest, QueryResponse } from '@/types'

// API Base URL configuration
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000"

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

// Main RAG query function
export async function queryRAG(params: QueryRequest): Promise<QueryResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    })

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      throw new RAGAPIError(
        `Query failed: ${errorText}`,
        response.status,
        'QUERY_ERROR'
      )
    }

    return await response.json()
  } catch (error) {
    if (error instanceof RAGAPIError) {
      throw error
    }
    throw new RAGAPIError(
      error instanceof Error ? error.message : 'Unknown error occurred',
      undefined,
      'NETWORK_ERROR'
    )
  }
}

// Health check function
export async function checkHealth(): Promise<boolean> {
  try {
    // Try multiple endpoints for compatibility
    const endpoints = ['/healthz', '/health', '/api/health'];

    for (const endpoint of endpoints) {
      try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        if (response.ok) return true;
      } catch {
        // Continue to next endpoint
      }
    }
    return false;
  } catch {
    return false;
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
