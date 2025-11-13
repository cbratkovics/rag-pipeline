'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card'
import { HelpCircle, TrendingUp, TrendingDown } from 'lucide-react'
import { Sparkline } from './Sparkline'
import type { LucideIcon } from 'lucide-react'

interface MetricKPIProps {
  title: string
  value: number
  unit?: string
  prefix?: string
  decimals?: number
  icon?: LucideIcon
  color?: string
  bgColor?: string
  delta?: number
  deltaLabel?: string
  helpText?: string
  sparklineData?: number[]
  target?: number
  targetLabel?: string
}

function useCountUp(end: number, duration: number = 1000, decimals: number = 0) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    let startTime: number | null = null
    const startValue = 0

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime
      const progress = Math.min((currentTime - startTime) / duration, 1)

      // Easing function for smooth animation
      const easeOutQuad = (t: number) => t * (2 - t)
      const easedProgress = easeOutQuad(progress)

      setCount(startValue + (end - startValue) * easedProgress)

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [end, duration])

  return count.toFixed(decimals)
}

export function MetricKPI({
  title,
  value,
  unit = '',
  prefix = '',
  decimals = 0,
  icon: Icon,
  color = 'text-blue-600',
  bgColor = 'bg-blue-50',
  delta,
  deltaLabel,
  helpText,
  sparklineData,
  target,
  targetLabel,
}: MetricKPIProps) {
  const animatedValue = useCountUp(value, 1000, decimals)
  const deltaIsPositive = delta !== undefined && delta > 0

  return (
    <Card className="border-2 hover:shadow-lg transition-all duration-200">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              {title}
            </CardTitle>
            {helpText && (
              <HoverCard>
                <HoverCardTrigger asChild>
                  <button className="text-gray-400 hover:text-gray-600 transition-colors">
                    <HelpCircle className="h-3 w-3" />
                  </button>
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <p className="text-sm text-gray-700">{helpText}</p>
                </HoverCardContent>
              </HoverCard>
            )}
          </div>
          {Icon && (
            <div className={`p-1.5 rounded-md ${bgColor}`}>
              <Icon className={`h-4 w-4 ${color}`} />
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-baseline gap-1">
          <span className={`text-3xl font-bold ${color} tabular-nums`}>
            {prefix}{animatedValue}
          </span>
          {unit && (
            <span className="text-sm font-normal text-gray-500">{unit}</span>
          )}
        </div>

        {delta !== undefined && (
          <div className="flex items-center gap-2">
            <Badge
              variant={deltaIsPositive ? "default" : "secondary"}
              className={`flex items-center gap-1 ${
                deltaIsPositive
                  ? 'bg-green-100 text-green-700 border-green-200'
                  : 'bg-blue-100 text-blue-700 border-blue-200'
              }`}
            >
              {deltaIsPositive ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              <span className="font-semibold">
                {deltaIsPositive ? '+' : ''}{delta}%
              </span>
            </Badge>
            {deltaLabel && (
              <span className="text-xs text-gray-500">{deltaLabel}</span>
            )}
          </div>
        )}

        {target !== undefined && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-gray-600">{targetLabel || 'Target'}</span>
              <span className="font-semibold text-gray-900">
                {prefix}{target}{unit}
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-1.5">
              <div
                className={`h-1.5 rounded-full transition-all duration-1000 ${
                  value >= target ? 'bg-green-500' : 'bg-blue-500'
                }`}
                style={{ width: `${Math.min((value / target) * 100, 100)}%` }}
              />
            </div>
          </div>
        )}

        {sparklineData && sparklineData.length > 0 && (
          <div className="pt-2">
            <Sparkline data={sparklineData} color={color.replace('text-', '')} />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
