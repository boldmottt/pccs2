'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/Button'
import { Plus, Layers } from 'lucide-react'
import { LayerEditorWithSelector, type LayerWithAddInk } from '@/components/samples/LayerEditorWithSelector'
import { ColorPreview } from '@/components/samples/ColorPreview'
import type { Layer } from '@/lib/types/project'
import { InkItem } from '@/lib/types/project'
import type { Ink } from '@/components/samples/InkSelector'

export default function NewSamplePage() {
  const router = useRouter()
  const [layers, setLayers] = useState<Layer[]>([])
  const [baseColor, setBaseColor] = useState({ L: 100, a: 0, b: 0 })
  const [inks, setInks] = useState<Ink[]>([]) // TODO: Fetch from API - for visualization

  const addLayer = () => {
    const newLayerNumber = layers.length + 1
    setLayers([...layers, {
      layerNumber: newLayerNumber,
      inkItems: [],
      printColorSci: { L: 0, a: 0, b: 0 },
      printColorSce: { L: 0, a: 0, b: 0 }
    }])
  }

  const updateLayer = (layerNumber: number, updates: Partial<Layer>) => {
    setLayers(layers.map(l =>
      l.layerNumber === layerNumber ? { ...l, ...updates } : l
    ))
  }

  const handleAddInk = (layerNumber: number, ink: Ink, amount: number) => {
    const layer = layers.find(l => l.layerNumber === layerNumber)
    if (layer) {
      const newInkItems: InkItem[] = [...layer.inkItems, { inkId: ink.inkId, amount }]
      updateLayer(layerNumber, { inkItems: newInkItems })
    }
  }

  const handleSave = async () => {
    console.log('Saving sample:', { layers, baseColor })
    // TODO: API call to save sample
    router.push('/samples')
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">샘플 등록</h1>
          <p className="text-gray-600 mt-1">배합비 레시피 작성</p>
        </div>
        <Button variant="outline" onClick={() => router.push('/samples')}>
          취소
        </Button>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">베이스 색상</h2>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">L</label>
                <input
                  type="number"
                  value={baseColor.L}
                  onChange={e => setBaseColor({ ...baseColor, L: Number(e.target.value) })}
                  className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg"
                  min="0"
                  max="100"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">a</label>
                <input
                  type="number"
                  value={baseColor.a}
                  onChange={e => setBaseColor({ ...baseColor, a: Number(e.target.value) })}
                  className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg"
                  min="-128"
                  max="127"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">b</label>
                <input
                  type="number"
                  value={baseColor.b}
                  onChange={e => setBaseColor({ ...baseColor, b: Number(e.target.value) })}
                  className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg"
                  min="-128"
                  max="127"
                />
              </div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Layers className="w-5 h-5" />
                배합비 레이어
              </h2>
              <Button onClick={addLayer} size="sm">
                <Plus className="w-4 h-4 mr-1" />
                레이어 추가
              </Button>
            </div>

            <div className="space-y-4">
              {layers.map(layer => (
                <LayerEditorWithSelector
                  key={layer.layerNumber}
                  layerNumber={layer.layerNumber}
                  inkItems={layer.inkItems}
                  inks={inks}
                  onInksChange={(items) => updateLayer(layer.layerNumber, { inkItems: items })}
                  onAddInk={(ink, amount) => handleAddInk(layer.layerNumber, ink, amount)}
                  onThinnerChange={(v) => updateLayer(layer.layerNumber, { thinnerPct: v })}
                  onHardenerChange={(v) => updateLayer(layer.layerNumber, { hardenerPct: v })}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-1">
          <ColorPreview
            layers={layers}
            baseColor={baseColor}
            onPredict={(prediction) => {
              const pred = prediction as any
              if (pred && pred.finalPrediction) {
                const updatedLayers = layers.map(l => ({
                  ...l,
                  printColorSci: pred.finalPrediction,
                  printColorSce: pred.finalPrediction
                }))
                setLayers(updatedLayers)
              }
            }}
          />

          <div className="mt-6">
            <Button
              onClick={handleSave}
              disabled={layers.length === 0 || layers.some(l => l.inkItems.length === 0)}
              className="w-full"
            >
              샘플 등록
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
