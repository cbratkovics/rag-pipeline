import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getConfidenceColor(score: number): string {
  if (score >= 0.8) return 'green'
  if (score >= 0.6) return 'yellow'
  return 'red'
}

export function getConfidenceLabel(score: number): string {
  if (score >= 0.8) return 'High'
  if (score >= 0.6) return 'Medium'
  return 'Low'
}

export function parseScoreAverage(scores: Record<string, number>): number {
  const values = Object.values(scores)
  if (!values.length) return 0
  return values.reduce((a, b) => a + b, 0) / values.length
}
