'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { X } from 'lucide-react'
import type { Ink, InkItem } from '@/lib/types/project'

interface LayerEditorProps {
  layerNumber: number
  inkItems: InkItem[]
  thinnerPct?: number
  hardenerPct?: number
  onInksChange: (items: InkItem[]) => void
  onThinnerChange: (value: number) => void
  onHardenerChange: (value: number) => void
  inks?: Ink[]
}

export function LayerEditor({
  layerNumber,
  inkItems,
  thinnerPct,
  hardenerPct,
  onInksChange,
  onThinnerChange,
  onHardenerChange,
  inks = []
}: LayerEditorProps) {
  const handleRemoveInk = (index: number) => {
    onInksChange(inkItems.filter((_, i) => i !== index))
  }

  const totalAmount = inkItems.reduce((sum, item) => sum + item.amount, 0)

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>{layerNumber}도</CardTitle>
          <span className="text-sm text-gray-500">총량: {totalAmount.toFixed(1)}g</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          {inkItems.length === 0 ? (
            <p className="text-sm text-gray-400 italic">잉크가 없습니다.</p>
          ) : (
            <div className="space-y-2">
              {inkItems.map((item, index) => {
                const inkInfo = inks.find(i => i.ink_id === item.ink_id)
                return (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <span className="font-medium">{inkInfo?.ink_name || item.ink_id}</span>
                      <span className="text-gray-500 ml-2">{item.amount.toFixed(1)}g</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveInk(index)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 pt-2">
          <div>
            <label className="block text-xs text-gray-500 mb-1">신너 (%)</label>
            <input
              type="number"
              value={thinnerPct || ''}
              onChange={e => onThinnerChange(Number(e.target.value))}
              className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
              min="0"
              max="100"
              step="0.1"
              placeholder="0"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">경화제 (%)</label>
            <input
              type="number"
              value={hardenerPct || ''}
              onChange={e => onHardenerChange(Number(e.target.value))}
              className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
              min="0"
              max="100"
              step="0.1"
              placeholder="0"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
