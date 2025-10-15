import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Utility function to merge Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format milliseconds to human-readable duration
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${Math.round(ms)}ms`
  }
  return `${(ms / 1000).toFixed(2)}s`
}

/**
 * Format USD cost with proper precision
 */
export function formatCost(usd: number): string {
  if (usd < 0.01) {
    return `$${(usd * 1000).toFixed(3)}m` // Show in millidollars
  }
  return `$${usd.toFixed(4)}`
}

/**
 * Calculate confidence score color
 */
export function getConfidenceColor(score: number): string {
  if (score >= 0.8) return 'text-green-600 bg-green-50'
  if (score >= 0.6) return 'text-amber-600 bg-amber-50'
  return 'text-red-600 bg-red-50'
}

/**
 * Get confidence label
 */
export function getConfidenceLabel(score: number): string {
  if (score >= 0.8) return 'High'
  if (score >= 0.6) return 'Medium'
  return 'Low'
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (error) {
    console.error('Failed to copy to clipboard:', error)
    return false
  }
}

/**
 * Generate random query ID
 */
export function generateQueryId(): string {
  return `q_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      func(...args)
    }

    if (timeout) {
      clearTimeout(timeout)
    }
    timeout = setTimeout(later, wait)
  }
}

/**
 * Format number with commas
 */
export function formatNumber(num: number): string {
  return new Intl.NumberFormat('en-US').format(num)
}

/**
 * Calculate average of array
 */
export function average(arr: number[]): number {
  if (arr.length === 0) return 0
  return arr.reduce((a, b) => a + b, 0) / arr.length
}

/**
 * Parse score object to average
 */
export function parseScoreAverage(scores: Record<string, number>): number {
  const values = Object.values(scores).filter(v => typeof v === 'number')
  return average(values)
}
