'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import type { Lab } from '@/lib/types/color'

export interface DataPoint {
  round: string
  L: number
  a: number
  b: number
  deltaE?: number
}

interface ColorTrendChartProps {
  dataPoints: DataPoint[]
  targetColor?: Lab
}

export function ColorTrendChart({ dataPoints, targetColor }: ColorTrendChartProps) {
  if (dataPoints.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center text-gray-400">
          데이터가 없습니다.
        </CardContent>
      </Card>
    )
  }

  const latest = dataPoints[dataPoints.length - 1]

  return (
    <Card>
      <CardHeader>
        <CardTitle>색상 추이 (라운드별)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Round summary table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3 font-medium text-gray-500">라운드</th>
                  <th className="text-center py-2 px-3 font-medium text-gray-500">L</th>
                  <th className="text-center py-2 px-3 font-medium text-gray-500">a</th>
                  <th className="text-center py-2 px-3 font-medium text-gray-500">b</th>
                  {targetColor && (
                    <th className="text-center py-2 px-3 font-medium text-gray-500">ΔE</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {dataPoints.map((point, index) => (
                  <tr
                    key={point.round}
                    className={`border-b border-gray-100 ${
                      index === dataPoints.length - 1 ? 'bg-blue-50' : ''
                    }`}
                  >
                    <td className="py-2 px-3">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        index === dataPoints.length - 1
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {point.round}
                      </span>
                    </td>
                    <td className="text-center py-2 px-3 font-medium">{point.L.toFixed(1)}</td>
                    <td className="text-center py-2 px-3 font-medium">{point.a.toFixed(1)}</td>
                    <td className="text-center py-2 px-3 font-medium">{point.b.toFixed(1)}</td>
                    {targetColor && point.deltaE !== undefined && (
                      <td className="text-center py-2 px-3">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          point.deltaE < 2
                            ? 'bg-green-100 text-green-700'
                            : point.deltaE < 5
                            ? 'bg-orange-100 text-orange-700'
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {point.deltaE.toFixed(2)}
                        </span>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Channel trend visualization */}
          <div>
            <div className="text-sm font-medium text-gray-700 mb-3">
              채널 추이
            </div>
            <div className="space-y-3">
              {(['L', 'a', 'b'] as const).map(channel => (
                <div key={channel} className="flex items-center gap-3">
                  <span className="w-8 text-xs font-medium text-gray-500">{channel}</span>
                  <div className="flex-1 relative h-8 bg-gray-100 rounded-lg overflow-hidden">
                    {/* Range indicators */}
                    <div
                      className="absolute top-0 bottom-0 bg-yellow-100/50"
                      style={{
                        left: `${Math.max(0, ((50 - 128) + 128) / 256 * 100)}%`,
                        right: `${Math.max(0, (100 - 50 + 128) / 256 * 100)}%`
                      }}
                    />
                    {/* Data points */}
                    {dataPoints.map((point, index) => {
                      const value = point[channel]
                      const isLatest = index === dataPoints.length - 1
                      const position = ((value + 128) / 256) * 100

                      return (
                        <div
                          key={index}
                          className={`absolute top-1 bottom-1 w-2 rounded-full transition-all ${
                            isLatest
                              ? 'bg-blue-500 z-10'
                              : 'bg-gray-400'
                          }`}
                          style={{ left: `calc(${position}% - 4px)` }}
                        />
                      )
                    })}
                  </div>
                  <span className="w-16 text-xs text-right text-gray-600 font-medium">
                    {latest[channel].toFixed(1)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Latest summary */}
          <div className="pt-4 border-t border-gray-200">
            <div className="text-sm font-medium text-gray-700 mb-2">
              최종 측정값
            </div>
            <div className="grid grid-cols-4 gap-2 text-center">
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">L</div>
                <div className="text-lg font-semibold">{latest.L.toFixed(1)}</div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">a</div>
                <div className="text-lg font-semibold">{latest.a.toFixed(1)}</div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">b</div>
                <div className="text-lg font-semibold">{latest.b.toFixed(1)}</div>
              </div>
              {targetColor && latest.deltaE !== undefined && (
                <div className="p-3 rounded-lg">
                  <div className="text-xs text-gray-500 mb-1">ΔE</div>
                  <div className={`text-lg font-semibold ${
                    latest.deltaE < 2
                      ? 'text-green-600'
                      : latest.deltaE < 5
                      ? 'text-orange-600'
                      : 'text-red-600'
                  }`}>
                    {latest.deltaE.toFixed(2)}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export interface ColorTrendChartSummary {
  minL: number
  maxL: number
  minA: number
  maxA: number
  minB: number
  maxB: number
  avgDeltaE: number
  bestRound: string
  worstDeltaE: number
}

export function calculateTrendSummary(dataPoints: DataPoint[], targetColor?: Lab): ColorTrendChartSummary | null {
  if (dataPoints.length === 0) return null

  const LValues = dataPoints.map(d => d.L)
  const aValues = dataPoints.map(d => d.a)
  const bValues = dataPoints.map(d => d.b)

  const deltaEValues = targetColor
    ? dataPoints.map(d => {
        const dl = d.L - targetColor.L
        const da = d.a - targetColor.a
        const db = d.b - targetColor.b
        return Math.sqrt(dl * dl + da * da + db * db)
      })
    : []

  return {
    minL: Math.min(...LValues),
    maxL: Math.max(...LValues),
    minA: Math.min(...aValues),
    maxA: Math.max(...aValues),
    minB: Math.min(...bValues),
    maxB: Math.max(...bValues),
    avgDeltaE: deltaEValues.length > 0
      ? deltaEValues.reduce((a, b) => a + b, 0) / deltaEValues.length
      : 0,
    bestRound: deltaEValues.length > 0
      ? dataPoints[deltaEValues.indexOf(Math.min(...deltaEValues))].round
      : dataPoints[0].round,
    worstDeltaE: deltaEValues.length > 0 ? Math.max(...deltaEValues) : 0
  }
}
