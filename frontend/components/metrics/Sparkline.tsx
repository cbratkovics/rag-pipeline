'use client'

import { LineChart, Line, ResponsiveContainer } from 'recharts'

interface SparklineProps {
  data: number[]
  color?: string
  height?: number
}

export function Sparkline({ data, color = 'blue-600', height = 40 }: SparklineProps) {
  // Transform array of numbers into recharts data format
  const chartData = data.map((value, index) => ({
    index,
    value,
  }))

  // Extract the color code (e.g., "blue-600" -> "#2563eb")
  const colorMap: Record<string, string> = {
    'blue-600': '#2563eb',
    'green-600': '#16a34a',
    'purple-600': '#9333ea',
    'indigo-600': '#4f46e5',
    'amber-600': '#d97706',
    'red-600': '#dc2626',
    'gray-600': '#4b5563',
  }

  const strokeColor = colorMap[color] || '#2563eb'

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={strokeColor}
          strokeWidth={2}
          dot={false}
          animationDuration={1000}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
