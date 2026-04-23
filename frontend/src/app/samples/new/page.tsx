'use client'

import { useState, useEffect, Suspense } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter, useSearchParams } from 'next/navigation'
import { samplesApi } from '@/lib/api/samples'
import { inksApi } from '@/lib/api/inks'
import { Button } from '@/components/ui/Button'

type InkItem = {
  inkId: string
  amount: number
}

type Layer = {
  layerNumber: number
  inkItems: InkItem[]
  thinnerPct: number | null
  hardenerPct: number | null
}

type FormData = {
  baseColorSci: { L: number; a: number; b: number }
  baseColorSce: { L: number; a: number; b: number }
  baseMaterial: string
  layers: Layer[]
}

export default function NewSamplePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">로딩 중...</div>}>
      <NewSampleContent />
    </Suspense>
  )
}

function NewSampleContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const queryClient = useQueryClient()
  const roundId = searchParams.get('roundId')

  const [formData, setFormData] = useState<FormData>({
    baseColorSci: { L: 0, a: 0, b: 0 },
    baseColorSce: { L: 0, a: 0, b: 0 },
    baseMaterial: '',
    layers: [],
  })

  const { data: inks = [] } = useQuery({
    queryKey: ['inks'],
    queryFn: () => inksApi.getAll(),
    enabled: !!roundId,
  })

  const mutation = useMutation({
    mutationFn: () => samplesApi.create(roundId!, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples'] })
      router.push(`/rounds/${roundId}`)
    },
    onError: (error: Error) => {
      console.error('Failed to create sample:', error)
    },
  })

  const addLayer = () => {
    const newLayerNumber = formData.layers.length + 1
    setFormData(prev => ({
      ...prev,
      layers: [
        ...prev.layers,
        {
          layerNumber: newLayerNumber,
          inkItems: [{ inkId: '', amount: 0 }],
          thinnerPct: null,
          hardenerPct: null,
        },
      ],
    }))
  }

  const removeLayer = (index: number) => {
    setFormData(prev => ({
      ...prev,
      layers: prev.layers
        .filter((_, i) => i !== index)
        .map((layer, i) => ({ ...layer, layerNumber: i + 1 })),
    }))
  }

  const addInkItem = (layerIndex: number) => {
    setFormData(prev => ({
      ...prev,
      layers: prev.layers.map((layer, i) => {
        if (i === layerIndex) {
          return {
            ...layer,
            inkItems: [...layer.inkItems, { inkId: '', amount: 0 }],
          }
        }
        return layer
      }),
    }))
  }

  const removeInkItem = (layerIndex: number, inkIndex: number) => {
    setFormData(prev => ({
      ...prev,
      layers: prev.layers.map((layer, i) => {
        if (i === layerIndex) {
          return {
            ...layer,
            inkItems: layer.inkItems.filter((_, j) => j !== inkIndex),
          }
        }
        return layer
      }),
    }))
  }

  const updateInkItem = (layerIndex: number, inkIndex: number, field: 'inkId' | 'amount', value: string | number) => {
    setFormData(prev => ({
      ...prev,
      layers: prev.layers.map((layer, i) => {
        if (i === layerIndex) {
          return {
            ...layer,
            inkItems: layer.inkItems.map((item, j) => {
              if (j === inkIndex) {
                return { ...item, [field]: value }
              }
              return item
            }),
          }
        }
        return layer
      }),
    }))
  }

  const updateLayer = (index: number, field: 'thinnerPct' | 'hardenerPct', value: string) => {
    setFormData(prev => ({
      ...prev,
      layers: prev.layers.map((layer, i) => {
        if (i === index) {
          return {
            ...layer,
            [field]: value ? parseFloat(value) : null,
          }
        }
        return layer
      }),
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate()
  }

  if (!roundId) {
    return <div className="p-8 text-center">roundId 가 필요합니다.</div>
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">새 샘플</h1>
      <p className="text-gray-600 mb-4">라운드: {roundId}</p>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="border rounded-lg p-4">
          <h3 className="font-semibold mb-3">기재 색상</h3>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-2">SCI</h4>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">L</label>
                  <input
                    type="number"
                    step="0.1"
                    min={0}
                    max={100}
                    value={formData.baseColorSci.L}
                    onChange={e => setFormData(prev => ({
                      ...prev,
                      baseColorSci: { ...prev.baseColorSci, L: parseFloat(e.target.value) || 0 },
                    }))}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">a</label>
                  <input
                    type="number"
                    step="0.1"
                    min={-128}
                    max={127}
                    value={formData.baseColorSci.a}
                    onChange={e => setFormData(prev => ({
                      ...prev,
                      baseColorSci: { ...prev.baseColorSci, a: parseFloat(e.target.value) || 0 },
                    }))}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">b</label>
                  <input
                    type="number"
                    step="0.1"
                    min={-128}
                    max={127}
                    value={formData.baseColorSci.b}
                    onChange={e => setFormData(prev => ({
                      ...prev,
                      baseColorSci: { ...prev.baseColorSci, b: parseFloat(e.target.value) || 0 },
                    }))}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-2">SCE</h4>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">L</label>
                  <input
                    type="number"
                    step="0.1"
                    min={0}
                    max={100}
                    value={formData.baseColorSce.L}
                    onChange={e => setFormData(prev => ({
                      ...prev,
                      baseColorSce: { ...prev.baseColorSce, L: parseFloat(e.target.value) || 0 },
                    }))}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">a</label>
                  <input
                    type="number"
                    step="0.1"
                    min={-128}
                    max={127}
                    value={formData.baseColorSce.a}
                    onChange={e => setFormData(prev => ({
                      ...prev,
                      baseColorSce: { ...prev.baseColorSce, a: parseFloat(e.target.value) || 0 },
                    }))}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">b</label>
                  <input
                    type="number"
                    step="0.1"
                    min={-128}
                    max={127}
                    value={formData.baseColorSce.b}
                    onChange={e => setFormData(prev => ({
                      ...prev,
                      baseColorSce: { ...prev.baseColorSce, b: parseFloat(e.target.value) || 0 },
                    }))}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold">레이어</h3>
            <Button type="button" onClick={addLayer} disabled={formData.layers.length >= 10}>
              레이어 추가
            </Button>
          </div>
          <div className="space-y-4">
            {formData.layers.map((layer, layerIndex) => (
              <div key={layerIndex} className="border rounded-lg p-4 bg-gray-50">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-medium">레이어 {layer.layerNumber}</h4>
                  <Button type="button" variant="outline" onClick={() => removeLayer(layerIndex)}>
                    삭제
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">시너%</label>
                    <input
                      type="number"
                      step="0.1"
                      min={0}
                      max={100}
                      value={layer.thinnerPct ?? ''}
                      onChange={e => updateLayer(layerIndex, 'thinnerPct', e.target.value)}
                      className="w-full border rounded-lg px-3 py-2"
                      placeholder="0-100"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">경화제%</label>
                    <input
                      type="number"
                      step="0.1"
                      min={0}
                      max={100}
                      value={layer.hardenerPct ?? ''}
                      onChange={e => updateLayer(layerIndex, 'hardenerPct', e.target.value)}
                      className="w-full border rounded-lg px-3 py-2"
                      placeholder="0-100"
                    />
                  </div>
                </div>
                <div className="mb-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium">잉크 항목</span>
                    <Button type="button" variant="outline" onClick={() => addInkItem(layerIndex)} className="text-xs">
                      + 잉크 추가
                    </Button>
                  </div>
                  <div className="space-y-2">
                    {layer.inkItems.map((inkItem, inkIndex) => (
                      <div key={inkIndex} className="flex gap-2 items-center">
                        <select
                          value={inkItem.inkId}
                          onChange={e => updateInkItem(layerIndex, inkIndex, 'inkId', e.target.value)}
                          className="flex-1 border rounded-lg px-2 py-1 text-sm"
                          required
                        >
                          <option value="">잉크 선택</option>
                          {inks.map((ink: any) => (
                            <option key={ink.inkId} value={ink.inkId}>
                              {ink.inkName} ({ink.inkCategory})
                            </option>
                          ))}
                        </select>
                        <input
                          type="number"
                          step="0.1"
                          min={0}
                          max={100}
                          value={inkItem.amount}
                          onChange={e => updateInkItem(layerIndex, inkIndex, 'amount', parseFloat(e.target.value) || 0)}
                          className="w-24 border rounded-lg px-2 py-1 text-sm"
                          placeholder="%"
                          required
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeInkItem(layerIndex, inkIndex)}
                        >
                          x
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
            {formData.layers.length === 0 && (
              <p className="text-gray-500 text-center py-4">레이어가 없습니다. &quot;레이어 추가&quot; 버튼을 클릭하세요.</p>
            )}
          </div>
        </div>

        <div className="flex gap-2">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? '생성 중...' : '샘플 생성'}
          </Button>
          <Button type="button" variant="outline" onClick={() => router.back()}>
            취소
          </Button>
        </div>
        {mutation.isError && (
          <p className="text-red-500 text-sm">생성 실패: {mutation.error.message}</p>
        )}
      </form>
    </div>
  )
}
