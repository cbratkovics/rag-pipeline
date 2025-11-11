'use client'

import { useEffect, useState } from 'react'
import { Badge } from './ui/badge'
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import { checkHealth } from '@/lib/api'

type HealthStatus = 'healthy' | 'unhealthy' | 'checking'

export function SystemStatus() {
  const [status, setStatus] = useState<HealthStatus>('checking')
  const [lastCheck, setLastCheck] = useState<Date>(new Date())

  useEffect(() => {
    // Initial health check
    checkSystemHealth()

    // Poll every 30 seconds
    const interval = setInterval(() => {
      checkSystemHealth()
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const checkSystemHealth = async () => {
    try {
      const isHealthy = await checkHealth()
      setStatus(isHealthy ? 'healthy' : 'unhealthy')
      setLastCheck(new Date())
    } catch (error) {
      setStatus('unhealthy')
      setLastCheck(new Date())
    }
  }

  const getStatusConfig = () => {
    switch (status) {
      case 'healthy':
        return {
          icon: CheckCircle2,
          text: 'All Systems Operational',
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
        }
      case 'unhealthy':
        return {
          icon: XCircle,
          text: 'API Unavailable',
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
        }
      case 'checking':
        return {
          icon: AlertCircle,
          text: 'Checking Status',
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
        }
    }
  }

  const config = getStatusConfig()
  const Icon = config.icon

  return (
    <div className="flex items-center gap-3">
      <Badge
        variant="outline"
        className={`${config.bgColor} ${config.borderColor} ${config.color} flex items-center gap-2`}
      >
        <span className="relative flex h-2 w-2">
          {status === 'healthy' && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          )}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${status === 'healthy' ? 'bg-green-500' : status === 'unhealthy' ? 'bg-red-500' : 'bg-yellow-500'}`}></span>
        </span>
        <Icon className="h-3 w-3" />
        <span className="text-xs font-medium">{config.text}</span>
      </Badge>
    </div>
  )
}
