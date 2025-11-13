'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Activity, TrendingUp, DollarSign, Clock } from 'lucide-react'

interface PerformanceGraphsProps {
  latestMetrics?: any
}

export function PerformanceGraphs({ latestMetrics }: PerformanceGraphsProps) {
  const [performanceData, setPerformanceData] = useState<any[]>([
    { time: '0s', latency: 450, throughput: 45, cacheHitRate: 85, cost: 0.002 },
    { time: '5s', latency: 520, throughput: 42, cacheHitRate: 82, cost: 0.0025 },
    { time: '10s', latency: 380, throughput: 48, cacheHitRate: 88, cost: 0.0018 },
    { time: '15s', latency: 410, throughput: 46, cacheHitRate: 86, cost: 0.0021 },
    { time: '20s', latency: 95, throughput: 52, cacheHitRate: 94, cost: 0.0005 },
  ])

  // Simulate real-time updates every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setPerformanceData(prev => {
        const newData = [...prev]
        if (newData.length > 10) newData.shift()

        const cacheHit = Math.random() > 0.3
        newData.push({
          time: `${newData.length * 5}s`,
          latency: cacheHit ? Math.random() * 150 + 50 : Math.random() * 800 + 400,
          throughput: Math.random() * 20 + 40,
          cacheHitRate: Math.random() * 15 + 80,
          cost: cacheHit ? Math.random() * 0.001 + 0.0005 : Math.random() * 0.003 + 0.002,
        })

        return newData
      })
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
      {/* Latency Trend */}
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-semibold">
            <Clock className="h-4 w-4 text-blue-500" />
            Response Latency Trend
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={performanceData}>
              <defs>
                <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="time" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  fontSize: '12px'
                }}
              />
              <Area
                type="monotone"
                dataKey="latency"
                stroke="#3b82f6"
                fill="url(#colorLatency)"
                strokeWidth={2}
                name="Latency (ms)"
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex justify-between text-xs text-gray-500 mt-3 px-1">
            <span>Avg: 450ms</span>
            <span>P95: 980ms</span>
            <span>P99: 1250ms</span>
          </div>
        </CardContent>
      </Card>

      {/* Cache Performance */}
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-semibold">
            <Activity className="h-4 w-4 text-green-500" />
            Cache Hit Rate
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="time" tick={{ fontSize: 11 }} />
              <YAxis domain={[70, 100]} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  fontSize: '12px'
                }}
              />
              <Line
                type="monotone"
                dataKey="cacheHitRate"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ fill: '#10b981', r: 3 }}
                name="Hit Rate (%)"
              />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex justify-between text-xs text-gray-500 mt-3 px-1">
            <span>Current: 85%</span>
            <span>Target: 90%</span>
            <span className="text-green-600 font-medium">Saved: $3,240/mo</span>
          </div>
        </CardContent>
      </Card>

      {/* Cost Tracking */}
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-semibold">
            <DollarSign className="h-4 w-4 text-yellow-500" />
            Cost per Query
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={performanceData}>
              <defs>
                <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#eab308" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#eab308" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="time" tick={{ fontSize: 11 }} />
              <YAxis
                domain={[0, 0.004]}
                tickFormatter={(v) => `$${v.toFixed(4)}`}
                tick={{ fontSize: 11 }}
              />
              <Tooltip
                formatter={(v: any) => `$${v.toFixed(4)}`}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  fontSize: '12px'
                }}
              />
              <Area
                type="stepAfter"
                dataKey="cost"
                stroke="#eab308"
                fill="url(#colorCost)"
                strokeWidth={2}
                name="Cost (USD)"
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex justify-between text-xs text-gray-500 mt-3 px-1">
            <span>Avg: $0.002</span>
            <span>Peak: $0.008</span>
            <span className="text-green-600 font-medium">Savings: 83%</span>
          </div>
        </CardContent>
      </Card>

      {/* Throughput */}
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-semibold">
            <TrendingUp className="h-4 w-4 text-purple-500" />
            Query Throughput
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="time" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  fontSize: '12px'
                }}
              />
              <Line
                type="monotone"
                dataKey="throughput"
                stroke="#a855f7"
                strokeWidth={2}
                dot={false}
                name="Queries/sec"
              />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex justify-between text-xs text-gray-500 mt-3 px-1">
            <span>Current: 45 QPS</span>
            <span>Peak: 120 QPS</span>
            <span>Capacity: 1000 QPS</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
