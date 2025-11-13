'use client'

import { Badge } from '@/components/ui/badge'
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card'

export type SystemStatus = 'operational' | 'degraded' | 'down'

interface LiveStatusDotProps {
  status: SystemStatus
  label?: string
  showLabel?: boolean
  lastChecked?: string
  uptime?: string
}

const statusConfig = {
  operational: {
    color: 'bg-green-500',
    textColor: 'text-green-700',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    label: 'Operational',
    description: 'All systems are functioning normally',
  },
  degraded: {
    color: 'bg-amber-500',
    textColor: 'text-amber-700',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    label: 'Degraded',
    description: 'Some systems are experiencing issues',
  },
  down: {
    color: 'bg-red-500',
    textColor: 'text-red-700',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    label: 'Down',
    description: 'System is currently unavailable',
  },
}

export function LiveStatusDot({
  status,
  label,
  showLabel = true,
  lastChecked,
  uptime,
}: LiveStatusDotProps) {
  const config = statusConfig[status]
  const displayLabel = label || config.label

  return (
    <HoverCard>
      <HoverCardTrigger asChild>
        <div className="flex items-center gap-2 cursor-pointer">
          <div className="relative flex items-center justify-center">
            {/* Pulsing background ring */}
            <div
              className={`absolute w-3 h-3 rounded-full ${config.color} opacity-25 animate-ping`}
            />
            {/* Solid dot */}
            <div className={`relative w-2 h-2 rounded-full ${config.color}`} />
          </div>
          {showLabel && (
            <Badge
              variant="outline"
              className={`${config.textColor} ${config.bgColor} ${config.borderColor} font-medium`}
            >
              {displayLabel}
            </Badge>
          )}
        </div>
      </HoverCardTrigger>
      <HoverCardContent className="w-64">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold">System Status</h4>
            <Badge
              variant="outline"
              className={`${config.textColor} ${config.bgColor} ${config.borderColor}`}
            >
              {config.label}
            </Badge>
          </div>
          <p className="text-xs text-gray-600">{config.description}</p>
          {lastChecked && (
            <div className="pt-2 border-t text-xs text-gray-500">
              <span className="font-medium">Last checked:</span> {lastChecked}
            </div>
          )}
          {uptime && (
            <div className="text-xs text-gray-500">
              <span className="font-medium">Uptime:</span> {uptime}
            </div>
          )}
        </div>
      </HoverCardContent>
    </HoverCard>
  )
}
