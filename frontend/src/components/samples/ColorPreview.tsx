'use client'

import { useState } from 'react'
import { predictApi, type PredictResponse } from '@/lib/api/predict'
import { getErrorMessage } from '@/lib/api/client'
import { ColorComparison } from '@/components/color/ColorComparison'
import { InkDonutChart, type InkData } from '@/components/visualization/InkDonutChart'
import { labToCss, type Lab } from '@/lib/types/color'
import type { Ink, Layer } from '@/lib/types/project'
import { Button } from '@/components/ui/Button'

interface ColorPreviewProps {
  layers: Layer[]
  baseColor: Lab
  onPredict?: (prediction: PredictResponse) => void
  inks?: Ink[]
}

// 잉크 ID에서 일관된 표시 색상 생성
function getColorForInk(inkId: string): string {
  const colors = [
    '#EF4444', '#F97316', '#F59E0B', '#84CC16',
    '#10B981', '#06B6D4', '#3B82F6', '#6366F1',
    '#8B5CF6', '#EC4899', '#F43F5E', '#A8A29E'
  ]
  let hash = 0
  for (let i = 0; i < inkId.length; i++) {
    hash = inkId.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

export function ColorPreview({ layers, baseColor, onPredict, inks = [] }: ColorPreviewProps) {
  const [prediction, setPrediction] = useState<PredictResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const inkName = (inkId: string) => inks.find(i => i.ink_id === inkId)?.ink_name || inkId

  // 측색값이 있으면 실제 잉크 색, 없으면 해시 팔레트 색
  const inkColor = (inkId: string) => {
    const sci = inks.find(i => i.ink_id === inkId)?.solid_color_sci
    return sci ? labToCss(sci) : getColorForInk(inkId)
  }

  const handlePredict = async () => {
    if (layers.length === 0 || layers.some(l => l.ink_items.length === 0)) {
      setError('모든 레이어에 잉크가 있어야 합니다.')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const result = await predictApi.predict({
        recipe: { layers: layers.map(l => ({ ink_items: l.ink_items })) },
        base_color: baseColor,
      })
      setPrediction(result)
      onPredict?.(result)
    } catch (err) {
      setError('예측 실패: ' + getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="border-t pt-6">
      <h3 className="text-lg font-semibold mb-4">색상 예측</h3>

      <div className="flex items-center gap-4 mb-6">
        <Button
          onClick={handlePredict}
          disabled={isLoading || layers.length === 0 || layers.some(l => l.ink_items.length === 0)}
          className="w-40"
        >
          {isLoading ? '예측 중...' : '예측 실행'}
        </Button>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm mb-4">
          {error}
        </div>
      )}

      {prediction && (
        <div className="space-y-6">
          <ColorComparison
            color1={baseColor}
            color2={prediction.final_prediction}
            label1="베이스"
            label2="예측"
            deltaE={prediction.delta_E}
          />

          <div className="pt-4 border-t">
            <h4 className="font-medium mb-3">예측 정보</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">KM 예측:</span>
                <div className="mt-1">
                  L: {prediction.km_prediction.L.toFixed(1)},
                  a: {prediction.km_prediction.a.toFixed(1)},
                  b: {prediction.km_prediction.b.toFixed(1)}
                </div>
              </div>
              <div>
                <span className="text-gray-500">ML 보정 신뢰도:</span>
                <div className="mt-1">{prediction.ml_confidence.toFixed(2)}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 레이어별 배합비 */}
      {layers.some(l => l.ink_items.length > 0) && (
        <div className="pt-4 mt-6 border-t">
          <h4 className="font-medium mb-3">레이어별 배합비</h4>
          <div className="space-y-4">
            {layers.map(layer => {
              const layerInks: InkData[] = layer.ink_items.map(item => ({
                inkId: item.ink_id,
                inkName: inkName(item.ink_id),
                amount: item.amount,
                color: inkColor(item.ink_id),
              }))
              const layerTotal = layerInks.reduce((sum, ink) => sum + ink.amount, 0)

              return (
                <div key={layer.layer_number} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h5 className="font-medium">{layer.layer_number}도</h5>
                    <span className="text-xs text-gray-500">총량: {layerTotal.toFixed(1)}g</span>
                  </div>
                  {layerInks.length > 0 ? (
                    <div className="flex items-center gap-4">
                      <InkDonutChart
                        inks={layerInks}
                        totalAmount={layerTotal}
                        size="sm"
                        showLabels={false}
                      />
                      <div className="flex-1 space-y-1">
                        {layerInks.map(item => (
                          <div key={item.inkId} className="flex items-center justify-between text-xs">
                            <div className="flex items-center gap-2">
                              <div
                                className="w-2 h-2 rounded-full"
                                style={{ backgroundColor: item.color ?? getColorForInk(item.inkId) }}
                              />
                              <span>{item.inkName}</span>
                            </div>
                            <span className="text-gray-500">
                              {item.amount.toFixed(1)}g ({layerTotal > 0 ? ((item.amount / layerTotal) * 100).toFixed(0) : 0}%)
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-400">잉크가 없습니다.</p>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
