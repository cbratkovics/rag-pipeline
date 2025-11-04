'use client'

import { useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Activity } from 'lucide-react'
import { Database } from 'lucide-react'
import { Zap } from 'lucide-react'
import { Server } from 'lucide-react'

export function SystemStatus() {
  const [status, setStatus] = useState({
    api: 'checking',
    redis: 'checking',
    vectorDb: 'checking',
    latency: 0
  })

  useEffect(() => {
    const checkHealth = async () => {
      const start = Date.now()
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/health`)
        const data = await res.json()
        setStatus({
          api: res.ok ? 'healthy' : 'degraded',
          redis: data.redis_connected ? 'connected' : 'disconnected',
          vectorDb: data.vector_store_ready ? 'ready' : 'loading',
          latency: Date.now() - start
        })
      } catch {
        setStatus(prev => ({ ...prev, api: 'offline', latency: 0 }))
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (value: string) => {
    if (value === 'healthy' || value === 'connected' || value === 'ready') return 'default'
    if (value === 'checking' || value === 'loading') return 'secondary'
    return 'destructive'
  }

  return (
    <div className="flex items-center gap-4 text-sm">
      <Badge variant={getStatusColor(status.api)}>
        <Server className="w-3 h-3 mr-1" />
        API: {status.api}
      </Badge>
      <Badge variant={getStatusColor(status.redis)}>
        <Zap className="w-3 h-3 mr-1" />
        Cache: {status.redis}
      </Badge>
      <Badge variant={getStatusColor(status.vectorDb)}>
        <Database className="w-3 h-3 mr-1" />
        Vector DB: {status.vectorDb}
      </Badge>
      {status.latency > 0 && (
        <Badge variant="outline">
          <Activity className="w-3 h-3 mr-1" />
          {status.latency}ms
        </Badge>
      )}
    </div>
  )
}
