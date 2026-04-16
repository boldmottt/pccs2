'use client'

import { useMemo } from 'react'
import { cn } from '@/lib/utils'

export interface InkData {
  inkId: string
  inkName: string
  amount: number
  color?: string
}

interface InkDonutChartProps {
  inks: InkData[]
  totalAmount: number
  size?: 'sm' | 'md' | 'lg'
  showLabels?: boolean
}

export function InkDonutChart({
  inks,
  totalAmount,
  size = 'md',
  showLabels = true
}: InkDonutChartProps) {
  const sizeClasses = {
    sm: 'w-24 h-24',
    md: 'w-40 h-40',
    lg: 'w-56 h-56'
  }

  const colors = useMemo(() => {
    const baseColors = [
      '#EF4444', '#F97316', '#F59E0B', '#84CC16',
      '#10B981', '#06B6D4', '#3B82F6', '#6366F1',
      '#8B5CF6', '#EC4899', '#F43F5E', '#A8A29E'
    ]
    return inks.map((_, i) => baseColors[i % baseColors.length])
  }, [inks])

  const { paths, labels } = useMemo(() => {
    if (totalAmount === 0) {
      return { paths: [], labels: [] }
    }

    let cumulativePercent = 0
    const totalPercent = 100

    const segmentPaths: string[] = []
    const segmentLabels: { label: string; percent: number; cx: number; cy: number }[] = []

    inks.forEach((ink, index) => {
      const portion = totalAmount > 0 ? (ink.amount / totalAmount) * 100 : 0
      const startPercent = cumulativePercent
      cumulativePercent += portion

      const startAngle = (startPercent / 100) * 2 * Math.PI
      const endAngle = (cumulativePercent / 100) * 2 * Math.PI

      const outerRadius = 40
      const innerRadius = 28
      const center = 50

      const startX = center + outerRadius * Math.cos(startAngle)
      const startY = center + outerRadius * Math.sin(startAngle)
      const endX = center + outerRadius * Math.cos(endAngle)
      const endY = center + outerRadius * Math.sin(endAngle)

      const innerStartX = center + innerRadius * Math.cos(endAngle)
      const innerStartY = center + innerRadius * Math.sin(endAngle)
      const innerEndX = center + innerRadius * Math.cos(startAngle)
      const innerEndY = center + innerRadius * Math.sin(startAngle)

      const largeArcFlag = portion > 50 ? 1 : 0

      const pathData = [
        `M ${startX} ${startY}`,
        `A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${endX} ${endY}`,
        `L ${innerStartX} ${innerStartY}`,
        `A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${innerEndX} ${innerEndY}`,
        'Z'
      ].join(' ')

      segmentPaths.push(pathData)

      if (showLabels && ink.amount > 0) {
        const midAngle = (startPercent + portion / 2) / 100 * 2 * Math.PI
        const labelRadius = (outerRadius + innerRadius) / 2
        const labelCx = center + labelRadius * Math.cos(midAngle)
        const labelCy = center + labelRadius * Math.sin(midAngle)

        segmentLabels.push({
          label: `${ink.inkName}: ${ink.amount.toFixed(1)}g`,
          percent: portion,
          cx: labelCx,
          cy: labelCy
        })
      }
    })

    return { paths: segmentPaths, labels: segmentLabels }
  }, [inks, totalAmount, showLabels])

  if (inks.length === 0) {
    return (
      <div className={cn('flex items-center justify-center rounded-full bg-gray-100', sizeClasses[size])}>
        <span className="text-xs text-gray-400">없음</span>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <svg
        viewBox="0 0 100 100"
        className={cn('transition-all duration-300', sizeClasses[size])}
      >
        {paths.map((path, index) => (
          <path
            key={inks[index]?.inkId || index}
            d={path}
            fill={inks[index]?.color || colors[index] || '#3B82F6'}
            className="hover:opacity-80 transition-opacity"
          />
        ))}
        {showLabels && labels.map((label, index) => (
          <text
            key={index}
            x={label.cx}
            y={label.cy}
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-xs fill-white font-medium"
            style={{ fontSize: '4px' }}
          >
            {label.label}
          </text>
        ))}
      </svg>
      <div className="text-xs text-gray-600">
        총량: {totalAmount.toFixed(1)}g
      </div>
    </div>
  )
}

interface InkLegendProps {
  inks: InkData[]
  size?: 'sm' | 'md'
}

export function InkLegend({ inks, size = 'sm' }: InkLegendProps) {
  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm'
  }

  const colors = useMemo(() => {
    const baseColors = [
      '#EF4444', '#F97316', '#F59E0B', '#84CC16',
      '#10B981', '#06B6D4', '#3B82F6', '#6366F1',
      '#8B5CF6', '#EC4899', '#F43F5E', '#A8A29E'
    ]
    return inks.map((_, i) => baseColors[i % baseColors.length])
  }, [inks])

  if (inks.length === 0) {
    return <div className="text-xs text-gray-400">잉크 목록 없음</div>
  }

  return (
    <div className="flex flex-col gap-1">
      {inks.map((ink, index) => (
        <div key={ink.inkId || index} className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: ink.color || colors[index] || '#3B82F6' }}
          />
          <span className={sizeClasses[size]}>
            {ink.inkName}: {ink.amount.toFixed(1)}g
          </span>
        </div>
      ))}
    </div>
  )
}
