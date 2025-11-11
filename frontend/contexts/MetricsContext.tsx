'use client'

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import type { MetricsState, QueryResult, HistoricalQuery } from '@/types'

interface MetricsContextValue extends MetricsState {
  addQuery: (result: QueryResult, question: string, provider: 'stub' | 'openai') => void
  recordCacheHit: () => void
  recordCacheMiss: () => void
  recordError: () => void
  clearMetrics: () => void
  getQueryHistory: () => HistoricalQuery[]
}

const MetricsContext = createContext<MetricsContextValue | undefined>(undefined)

const STORAGE_KEY = 'rag_pipeline_metrics'
const HISTORY_KEY = 'rag_pipeline_history'
const MAX_HISTORY = 20

function loadFromStorage<T>(key: string, defaultValue: T): T {
  if (typeof window === 'undefined') return defaultValue
  try {
    const stored = localStorage.getItem(key)
    return stored ? JSON.parse(stored) : defaultValue
  } catch {
    return defaultValue
  }
}

function saveToStorage(key: string, value: unknown): void {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (error) {
    console.warn('Failed to save to localStorage:', error)
  }
}

export function MetricsProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<MetricsState>(() => ({
    queries: [],
    cacheHits: loadFromStorage('cacheHits', 0),
    cacheMisses: loadFromStorage('cacheMisses', 0),
    totalQueries: loadFromStorage('totalQueries', 0),
    avgLatency: loadFromStorage('avgLatency', 0),
    errorCount: loadFromStorage('errorCount', 0),
    lastUpdated: new Date(),
    totalTokens: loadFromStorage('totalTokens', 0),
    totalCost: loadFromStorage('totalCost', 0),
  }))

  // Persist state to localStorage
  useEffect(() => {
    saveToStorage(STORAGE_KEY, {
      cacheHits: state.cacheHits,
      cacheMisses: state.cacheMisses,
      totalQueries: state.totalQueries,
      avgLatency: state.avgLatency,
      errorCount: state.errorCount,
      totalTokens: state.totalTokens,
      totalCost: state.totalCost,
    })
  }, [state])

  const addQuery = useCallback((result: QueryResult, question: string, provider: 'stub' | 'openai') => {
    setState(prev => {
      const newQueries = [...prev.queries, result].slice(-10) // Keep last 10
      const newTotal = prev.totalQueries + 1
      const newAvgLatency = (prev.avgLatency * prev.totalQueries + result.latency_ms) / newTotal

      // Estimate tokens (rough approximation: ~4 chars per token)
      const estimatedTokens = Math.ceil((result.answer.length + result.contexts.join('').length) / 4)
      const newTotalTokens = prev.totalTokens + estimatedTokens

      // Calculate cost
      const costPerToken = provider === 'openai' ? 0.002 / 1000 : 0.0015 / 1000
      const queryCost = estimatedTokens * costPerToken
      const newTotalCost = prev.totalCost + queryCost

      // Save to history
      const history = loadFromStorage<HistoricalQuery[]>(HISTORY_KEY, [])
      const newHistory = [
        ...history,
        {
          id: `query_${Date.now()}`,
          question,
          result,
          timestamp: new Date(),
          provider,
        },
      ].slice(-MAX_HISTORY)
      saveToStorage(HISTORY_KEY, newHistory)

      return {
        ...prev,
        queries: newQueries,
        totalQueries: newTotal,
        avgLatency: newAvgLatency,
        lastUpdated: new Date(),
        totalTokens: newTotalTokens,
        totalCost: newTotalCost,
      }
    })
  }, [])

  const recordCacheHit = useCallback(() => {
    setState(prev => ({ ...prev, cacheHits: prev.cacheHits + 1, lastUpdated: new Date() }))
  }, [])

  const recordCacheMiss = useCallback(() => {
    setState(prev => ({ ...prev, cacheMisses: prev.cacheMisses + 1, lastUpdated: new Date() }))
  }, [])

  const recordError = useCallback(() => {
    setState(prev => ({ ...prev, errorCount: prev.errorCount + 1, lastUpdated: new Date() }))
  }, [])

  const clearMetrics = useCallback(() => {
    setState({
      queries: [],
      cacheHits: 0,
      cacheMisses: 0,
      totalQueries: 0,
      avgLatency: 0,
      errorCount: 0,
      lastUpdated: new Date(),
      totalTokens: 0,
      totalCost: 0,
    })
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY)
      localStorage.removeItem(HISTORY_KEY)
    }
  }, [])

  const getQueryHistory = useCallback((): HistoricalQuery[] => {
    return loadFromStorage<HistoricalQuery[]>(HISTORY_KEY, [])
  }, [])

  const value: MetricsContextValue = {
    ...state,
    addQuery,
    recordCacheHit,
    recordCacheMiss,
    recordError,
    clearMetrics,
    getQueryHistory,
  }

  return <MetricsContext.Provider value={value}>{children}</MetricsContext.Provider>
}

export function useMetrics() {
  const context = useContext(MetricsContext)
  if (context === undefined) {
    throw new Error('useMetrics must be used within a MetricsProvider')
  }
  return context
}
