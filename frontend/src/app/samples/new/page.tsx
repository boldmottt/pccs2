'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Plus, Trash2, Layers } from 'lucide-react'
import { samplesApi, type SampleCreate } from '@/lib/api/samples'
import { inksApi, type InkResponse } from '@/lib/api/inks'
import { Select } from '@/components/ui/Select'

interface LayerData {
  layerNumber: number
  inkItems: { inkId: string; amount: number }[]
  thinnerPct?: number | ''
  hardenerPct?: number | ''
}

interface BaseColor {
  L: number
  a: number
  b: number
}

export default function NewSamplePage() {
  const router = useRouter()
  const [activeLayer, setActiveLayer] = useState<number>(1)
  const [baseColor, setBaseColor] = useState<BaseColor>({ L: 100, a: 0, b: 0 })
  const [layers, setLayers] = useState<LayerData[]>([])
  const [selectedInkId, setSelectedInkId] = useState<string>('')
  const [inkAmount, setInkAmount] = useState<number>(10)
  const [thinnerPct, setThinnerPct] = useState<number | ''>('')
  const [hardenerPct, setHardenerPct] = useState<number | ''>('')
  const [submitting, setSubmitting] = useState(false)
  const [roundId, setRoundId] = useState<string>('')

  // Load inks from API
  const { data: inks, isLoading: loadingInks } = useQuery({
    queryKey: ['inks'],
    queryFn: () => inksApi.getAll(),
  })

  // Add new layer
  const addLayer = () => {
    const newLayerNumber = layers.length + 1
    setLayers([...layers, {
      layerNumber: newLayerNumber,
      inkItems: [],
      thinnerPct: undefined,
      hardenerPct: undefined,
    }])
    setActiveLayer(newLayerNumber)
  }

  // Remove layer
  const removeLayer = (layerNumber: number) => {
    const updatedLayers = layers.filter(l => l.layerNumber !== layerNumber)
    setLayers(updatedLayers)
    if (activeLayer === layerNumber && updatedLayers.length > 0) {
      setActiveLayer(updatedLayers[updatedLayers.length - 1].layerNumber)
    }
  }

  // Get current layer
  const getCurrentLayer = () => {
    return layers.find(l => l.layerNumber === activeLayer) || null
  }

  // Add ink to current layer
  const handleAddInk = () => {
    const layer = getCurrentLayer()
    if (!layer || !selectedInkId) return

    const existingIndex = layer.inkItems.findIndex(i => i.inkId === selectedInkId)
    if (existingIndex >= 0) {
      // Update existing ink amount
      const updatedInkItems = [...layer.inkItems]
      updatedInkItems[existingIndex] = {
        ...updatedInkItems[existingIndex],
        amount: updatedInkItems[existingIndex].amount + inkAmount,
      }
      const updatedLayers = layers.map(l =>
        l.layerNumber === activeLayer ? { ...l, inkItems: updatedInkItems } : l
      )
      setLayers(updatedLayers)
    } else {
      // Add new ink
      setLayers([...layers, {
        ...layer,
        inkItems: [...layer.inkItems, { inkId: selectedInkId, amount: inkAmount }],
      }])
    }
    setInkAmount(10)
  }

  // Remove ink from layer
  const removeInkFromLayer = (layerNumber: number, inkId: string) => {
    setLayers(layers.map(l =>
      l.layerNumber === layerNumber
        ? { ...l, inkItems: l.inkItems.filter(i => i.inkId !== inkId) }
        : l
    ))
  }

  // Update thinner percentage
  const handleThinnerChange = (value: number | '' | undefined) => {
    setLayers(layers.map(l =>
      l.layerNumber === activeLayer ? { ...l, thinnerPct: value ?? '' } : l
    ))
    setThinnerPct(value ?? '')
  }

  // Update hardener percentage
  const handleHardenerChange = (value: number | '' | undefined) => {
    setLayers(layers.map(l =>
      l.layerNumber === activeLayer ? { ...l, hardenerPct: value ?? '' } : l
    ))
    setHardenerPct(value ?? '')
  }

  // Calculate total percentage for layer
  const calculateTotalPercentage = (layer: LayerData): number => {
    const inkTotal = layer.inkItems.reduce((sum, item) => sum + item.amount, 0)
    const thinner = typeof layer.thinnerPct === 'number' ? layer.thinnerPct : 0
    const hardener = typeof layer.hardenerPct === 'number' ? layer.hardenerPct : 0
    return inkTotal + thinner + hardener
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (layers.length === 0) {
      alert('최소 하나의 배합비를 입력해주세요.')
      return
    }

    // Validate layers
    for (const layer of layers) {
      if (layer.inkItems.length === 0) {
        alert(`${layer.layerNumber} 도에 잉크를 입력해주세요.`)
        return
      }
      const total = calculateTotalPercentage(layer)
      if (Math.abs(total - 100) > 1) {
        alert(`${layer.layerNumber} 도 배합비 합계가 100% 가 아닙니다. (현재: ${total.toFixed(1)}%)`)
        return
      }
    }

    setSubmitting(true)

    try {
      const sampleData: SampleCreate = {
        round_id: roundId || 'default',
        sample_number: 1,
        base_color_sci: baseColor,
        base_color_sce: baseColor,
        base_material: 'unknown',
        layers: layers.map(layer => ({
          layer_number: layer.layerNumber,
          ink_items: layer.inkItems.map(item => ({ ink_id: item.inkId, amount: item.amount })),
          thinner_pct: layer.thinnerPct === '' ? undefined : layer.thinnerPct,
          hardener_pct: layer.hardenerPct === '' ? undefined : layer.hardenerPct,
        })),
      }

      await samplesApi.create(roundId || 'default', sampleData)
      router.push('/samples')
    } catch (error) {
      console.error('Failed to save sample:', error)
      alert('샘플 저장에 실패했습니다.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">샘플 등록</h1>
          <p className="text-text-secondary">배합비 레시피를 작성하세요</p>
        </div>
        <Button variant="ghost" onClick={() => router.push('/samples')}>
          취소
        </Button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Base Color */}
            <div className="bg-bg-secondary/50 backdrop-blur-sm border border-border-subtle rounded-xl p-6">
              <h2 className="text-xl font-semibold mb-4">베이스 색상 (SCI/SCE)</h2>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1">
                    L (0-100)
                  </label>
                  <Input
                    type="number"
                    value={baseColor.L}
                    onChange={(e) => setBaseColor({ ...baseColor, L: Number(e.target.value) })}
                    min="0"
                    max="100"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1">
                    a (-128~127)
                  </label>
                  <Input
                    type="number"
                    value={baseColor.a}
                    onChange={(e) => setBaseColor({ ...baseColor, a: Number(e.target.value) })}
                    min="-128"
                    max="127"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1">
                    b (-128~127)
                  </label>
                  <Input
                    type="number"
                    value={baseColor.b}
                    onChange={(e) => setBaseColor({ ...baseColor, b: Number(e.target.value) })}
                    min="-128"
                    max="127"
                    step="0.1"
                  />
                </div>
              </div>
            </div>

            {/* Layer List */}
            <div className="bg-bg-secondary/50 backdrop-blur-sm border border-border-subtle rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <Layers className="w-5 h-5" />
                  배합비 레이어
                </h2>
                <Button type="button" onClick={addLayer} variant="secondary">
                  <Plus className="w-4 h-4 mr-1" />
                  레이어 추가
                </Button>
              </div>

              {layers.length === 0 ? (
                <div className="text-center py-8 text-text-secondary">
                  레이어가 없습니다. '레이어 추가' 버튼을 눌러주세요.
                </div>
              ) : (
                <div className="space-y-4">
                  {layers.map((layer) => (
                    <div
                      key={layer.layerNumber}
                      className={`border rounded-lg p-4 transition-all ${
                        activeLayer === layer.layerNumber
                          ? 'border-accent-primary bg-bg-tertiary/50'
                          : 'border-border-subtle hover:border-border-subtle'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <button
                            type="button"
                            onClick={() => setActiveLayer(layer.layerNumber)}
                            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                              activeLayer === layer.layerNumber
                                ? 'bg-accent-primary text-white'
                                : 'bg-bg-secondary text-text-secondary hover:text-text-primary'
                            }`}
                          >
                            {layer.layerNumber} 도
                          </button>
                          <span className="text-sm text-text-secondary">
                            잉크 {layer.inkItems.length} 종, 총 {calculateTotalPercentage(layer).toFixed(1)}%
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeLayer(layer.layerNumber)}
                          className="text-error hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>

                      {/* Ink Items */}
                      {layer.inkItems.length > 0 && (
                        <div className="bg-bg-secondary rounded-lg p-3 mb-3">
                          <div className="text-xs text-text-secondary mb-2">등록된 잉크:</div>
                          <div className="space-y-2">
                            {layer.inkItems.map((item) => {
                              const ink = inks?.find(i => i.ink_id === item.inkId)
                              return (
                                <div key={item.inkId} className="flex items-center justify-between text-sm">
                                  <span className="text-text-primary">
                                    {ink?.ink_name || item.inkId}
                                  </span>
                                  <div className="flex items-center gap-3">
                                    <span className="text-text-secondary">
                                      {item.amount.toFixed(1)}g
                                    </span>
                                    <button
                                      type="button"
                                      onClick={() => removeInkFromLayer(layer.layerNumber, item.inkId)}
                                      className="text-error hover:text-red-400"
                                    >
                                      제거
                                    </button>
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )}

                      {/* Add Ink Form */}
                      <div className="flex flex-wrap gap-3 items-end bg-bg-secondary rounded-lg p-3">
                        <div className="flex-1 min-w-[200px]">
                          <label className="block text-xs text-text-secondary mb-1">
                            잉크 선택
                          </label>
                          <Select
                            value={selectedInkId}
                            onValueChange={setSelectedInkId}
                            options={inks?.map(i => ({ value: i.ink_id, label: i.ink_name })) || []}
                            placeholder="잉크 선택"
                          />
                        </div>
                        <div className="w-24">
                          <label className="block text-xs text-text-secondary mb-1">
                            양 (g)
                          </label>
                          <Input
                            type="number"
                            value={inkAmount}
                            onChange={(e) => setInkAmount(Math.max(0, Number(e.target.value)))}
                            min="0"
                            step="0.1"
                          />
                        </div>
                        <Button
                          type="button"
                          onClick={handleAddInk}
                          disabled={!selectedInkId || inkAmount <= 0}
                          variant="secondary"
                        >
                          추가
                        </Button>
                      </div>

                      {/* Thinner & Hardener */}
                      <div className="flex flex-wrap gap-3 mt-3">
                        <div className="flex-1 min-w-[120px]">
                          <label className="block text-xs text-text-secondary mb-1">
                            신너 (%)
                          </label>
                          <Input
                            type="number"
                            value={thinnerPct}
                            onChange={(e) => handleThinnerChange(
                              e.target.value === '' ? '' : Math.max(0, Number(e.target.value))
                            )}
                            min="0"
                            max="100"
                            step="0.1"
                            placeholder="0"
                          />
                        </div>
                        <div className="flex-1 min-w-[120px]">
                          <label className="block text-xs text-text-secondary mb-1">
                            경화제 (%)
                          </label>
                          <Input
                            type="number"
                            value={hardenerPct}
                            onChange={(e) => handleHardenerChange(
                              e.target.value === '' ? '' : Math.max(0, Number(e.target.value))
                            )}
                            min="0"
                            max="100"
                            step="0.1"
                            placeholder="0"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Layer Info */}
            {getCurrentLayer() && (
              <div className="bg-bg-secondary/50 backdrop-blur-sm border border-border-subtle rounded-xl p-6">
                <h3 className="text-lg font-semibold mb-4">현재 레이어 정보</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-text-secondary">레이어:</span>
                    <span className="text-text-primary">{getCurrentLayer()?.layerNumber} 도</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">잉크 종류:</span>
                    <span className="text-text-primary">{getCurrentLayer()?.inkItems.length || 0} 종</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">합계:</span>
                    <span className={`font-medium ${
                      calculateTotalPercentage(getCurrentLayer()!) === 100
                        ? 'text-success'
                        : 'text-warning'
                    }`}>
                      {calculateTotalPercentage(getCurrentLayer()!).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={submitting || layers.length === 0}
              className="w-full"
            >
              {submitting ? '저장 중...' : '샘플 등록'}
            </Button>

            {/* Validation Note */}
            <div className="bg-bg-tertiary/50 border border-border-subtle rounded-lg p-4">
              <p className="text-xs text-text-secondary">
                ⚠️ 각 레이어의 배합비 합계가 100% 여야 합니다.
              </p>
            </div>
          </div>
        </div>
      </form>
    </div>
  )
}
