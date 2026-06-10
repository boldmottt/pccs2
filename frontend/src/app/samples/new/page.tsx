'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { samplesApi } from '@/lib/api/samples'
import { patternsApi } from '@/lib/api/patterns'
import { roundsApi } from '@/lib/api/rounds'
import { inksApi } from '@/lib/api/inks'
import { getErrorMessage } from '@/lib/api/client'
import type { Ink, InkItem, Layer, SampleCreate } from '@/lib/types/project'
import type { Lab } from '@/lib/types/color'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'
import { LayerEditorWithSelector } from '@/components/samples/LayerEditorWithSelector'
import { ColorPreview } from '@/components/samples/ColorPreview'
import { Plus, Layers, X, BadgePlus } from 'lucide-react'

const COPIED_LAYER_KEY = 'pccs2-copied-layer'

function LabInputs({
  label,
  value,
  onChange,
}: {
  label: string
  value: Lab
  onChange: (value: Lab) => void
}) {
  return (
    <div>
      <p className="text-xs text-gray-500 font-medium mb-2">{label}</p>
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">L*</label>
          <input
            type="number"
            value={value.L}
            onChange={e => onChange({ ...value, L: Number(e.target.value) })}
            className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
            min="0"
            max="100"
            step="0.01"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">a*</label>
          <input
            type="number"
            value={value.a}
            onChange={e => onChange({ ...value, a: Number(e.target.value) })}
            className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
            min="-128"
            max="127"
            step="0.01"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">b*</label>
          <input
            type="number"
            value={value.b}
            onChange={e => onChange({ ...value, b: Number(e.target.value) })}
            className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
            min="-128"
            max="127"
            step="0.01"
          />
        </div>
      </div>
    </div>
  )
}

/** 레이어 배합을 마스터 잉크로 등록하는 인라인 폼 */
function RegisterBlendForm({ layer }: { layer: Layer }) {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [inkName, setInkName] = useState('')

  const mutation = useMutation({
    mutationFn: (name: string) =>
      inksApi.registerBlend(crypto.randomUUID(), {
        ink_name: name,
        ink_category: 'COLOR',
        blend_recipe: { ink_items: layer.ink_items },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inks'] })
      setInkName('')
      setOpen(false)
    },
  })

  if (!open) {
    return (
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setOpen(true)}
          disabled={layer.ink_items.length === 0}
        >
          <BadgePlus className="w-4 h-4 mr-1" />
          마스터 잉크로 등록
        </Button>
        {mutation.isSuccess && (
          <span className="text-sm text-green-600">마스터 잉크로 등록되었습니다.</span>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-end gap-2">
        <div className="flex-1 max-w-xs">
          <label className="block text-xs text-gray-500 mb-1">잉크 이름</label>
          <input
            type="text"
            value={inkName}
            onChange={e => setInkName(e.target.value)}
            placeholder="예: 커스텀 레드 블렌드"
            className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600 text-sm"
            autoFocus
          />
        </div>
        <Button
          size="sm"
          className="h-10"
          onClick={() => inkName.trim() && mutation.mutate(inkName.trim())}
          disabled={!inkName.trim() || mutation.isPending}
        >
          {mutation.isPending ? '등록 중...' : '등록'}
        </Button>
        <Button variant="ghost" size="sm" className="h-10" onClick={() => setOpen(false)}>
          <X className="w-4 h-4" />
        </Button>
      </div>
      {mutation.isError && (
        <p className="text-sm text-red-600">등록 실패: {getErrorMessage(mutation.error)}</p>
      )}
    </div>
  )
}

/** round_id가 없을 때 패턴 → 라운드 선택/생성 UI */
function RoundPicker({ onRoundSelected }: { onRoundSelected: (roundId: string) => void }) {
  const queryClient = useQueryClient()
  const [patternId, setPatternId] = useState('')

  const patternsQuery = useQuery({
    queryKey: ['patterns'],
    queryFn: () => patternsApi.list(),
  })

  const roundsQuery = useQuery({
    queryKey: ['rounds', patternId],
    queryFn: () => roundsApi.list({ pattern_id: patternId }),
    enabled: !!patternId,
  })

  const createRoundMutation = useMutation({
    mutationFn: () => roundsApi.create(patternId),
    onSuccess: round => {
      queryClient.invalidateQueries({ queryKey: ['rounds', patternId] })
      onRoundSelected(round.round_id)
    },
  })

  const selectedPattern = patternsQuery.data?.find(p => p.pattern_id === patternId)

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <h2 className="text-lg font-semibold mb-4">라운드 선택</h2>

      {patternsQuery.isLoading ? (
        <p className="text-sm text-gray-500">패턴을 불러오는 중...</p>
      ) : patternsQuery.isError ? (
        <div className="text-sm">
          <p className="text-red-600 mb-2">{getErrorMessage(patternsQuery.error)}</p>
          <Button variant="outline" size="sm" onClick={() => patternsQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="max-w-sm">
            <label className="block text-sm font-medium text-gray-700 mb-1">패턴</label>
            <Select value={patternId} onValueChange={setPatternId}>
              <SelectTrigger>
                <SelectValue placeholder="패턴 선택">{selectedPattern?.pattern_name}</SelectValue>
              </SelectTrigger>
              <SelectContent>
                {(patternsQuery.data ?? []).map(pattern => (
                  <SelectItem key={pattern.pattern_id} value={pattern.pattern_id}>
                    {pattern.pattern_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {patternId && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">라운드</label>
              {roundsQuery.isLoading ? (
                <p className="text-sm text-gray-500">라운드를 불러오는 중...</p>
              ) : roundsQuery.isError ? (
                <div className="text-sm">
                  <p className="text-red-600 mb-2">{getErrorMessage(roundsQuery.error)}</p>
                  <Button variant="outline" size="sm" onClick={() => roundsQuery.refetch()}>
                    다시 시도
                  </Button>
                </div>
              ) : (
                <div className="flex flex-wrap items-center gap-2">
                  {(roundsQuery.data ?? []).map(round => (
                    <Button
                      key={round.round_id}
                      variant="outline"
                      size="sm"
                      onClick={() => onRoundSelected(round.round_id)}
                    >
                      라운드 {round.round_number}
                    </Button>
                  ))}
                  <Button
                    size="sm"
                    onClick={() => createRoundMutation.mutate()}
                    disabled={createRoundMutation.isPending}
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    {createRoundMutation.isPending ? '생성 중...' : '새 라운드'}
                  </Button>
                </div>
              )}
              {createRoundMutation.isError && (
                <p className="text-sm text-red-600 mt-2">
                  라운드 생성 실패: {getErrorMessage(createRoundMutation.error)}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function NewSampleForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const queryClient = useQueryClient()

  const [roundId, setRoundId] = useState(searchParams.get('round_id') ?? '')
  const [layers, setLayers] = useState<Layer[]>([])
  const [baseSci, setBaseSci] = useState<Lab>({ L: 100, a: 0, b: 0 })
  const [baseSce, setBaseSce] = useState<Lab>({ L: 100, a: 0, b: 0 })
  const [baseMaterial, setBaseMaterial] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  // 샘플 목록에서 복사한 배합비가 있으면 첫 레이어로 채움.
  // sessionStorage는 클라이언트에서만 읽을 수 있어 lazy initializer를 쓰면
  // 프리렌더 HTML과 hydration 불일치가 발생하므로, 마운트 후 1회성 setState가 의도된 동작이다.
  useEffect(() => {
    const copied = sessionStorage.getItem(COPIED_LAYER_KEY)
    if (!copied) return
    sessionStorage.removeItem(COPIED_LAYER_KEY)
    try {
      const layer = JSON.parse(copied) as Layer
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLayers([{ ...layer, layer_number: 1 }])
    } catch {
      // 잘못된 데이터는 무시
    }
  }, [])

  const inksQuery = useQuery({
    queryKey: ['inks'],
    queryFn: () => inksApi.list(),
  })

  const inks: Ink[] = inksQuery.data ?? []

  const createMutation = useMutation({
    mutationFn: (data: SampleCreate) => samplesApi.create(roundId, data),
    onSuccess: created => {
      queryClient.invalidateQueries({ queryKey: ['samples'] })
      router.push(`/patterns/${created.pattern_id}`)
    },
  })

  const addLayer = () => {
    setLayers(prev => [...prev, { layer_number: prev.length + 1, ink_items: [] }])
  }

  const removeLayer = (layerNumber: number) => {
    setLayers(prev =>
      prev
        .filter(l => l.layer_number !== layerNumber)
        .map((l, index) => ({ ...l, layer_number: index + 1 })),
    )
  }

  const updateLayer = (layerNumber: number, updates: Partial<Layer>) => {
    setLayers(prev => prev.map(l => (l.layer_number === layerNumber ? { ...l, ...updates } : l)))
  }

  const handleAddInk = (layerNumber: number, ink: Ink, amount: number) => {
    const layer = layers.find(l => l.layer_number === layerNumber)
    if (layer) {
      const newInkItems: InkItem[] = [...layer.ink_items, { ink_id: ink.ink_id, amount }]
      updateLayer(layerNumber, { ink_items: newInkItems })
    }
  }

  const handleSave = () => {
    setFormError(null)
    if (!roundId) {
      setFormError('라운드를 먼저 선택하세요.')
      return
    }
    if (!baseMaterial.trim()) {
      setFormError('베이스 소재를 입력하세요.')
      return
    }
    if (layers.length === 0 || layers.some(l => l.ink_items.length === 0)) {
      setFormError('모든 레이어에 잉크를 1개 이상 추가하세요.')
      return
    }
    createMutation.mutate({
      base_color_sci: baseSci,
      base_color_sce: baseSce,
      base_material: baseMaterial.trim(),
      layers,
    })
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

      {!roundId && <RoundPicker onRoundSelected={setRoundId} />}

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-4">
            <h2 className="text-lg font-semibold">베이스 색상</h2>
            <LabInputs label="베이스 측색값 SCI" value={baseSci} onChange={setBaseSci} />
            <LabInputs label="베이스 측색값 SCE" value={baseSce} onChange={setBaseSce} />
            <Input
              label="베이스 소재 *"
              placeholder="예: ABS"
              value={baseMaterial}
              onChange={e => setBaseMaterial(e.target.value)}
            />
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

            {inksQuery.isLoading ? (
              <div className="p-6 text-center text-gray-500 bg-white rounded-lg border border-gray-200">
                잉크 목록을 불러오는 중...
              </div>
            ) : inksQuery.isError ? (
              <div className="p-6 text-center bg-white rounded-lg border border-gray-200">
                <p className="text-red-600 mb-3">{getErrorMessage(inksQuery.error)}</p>
                <Button variant="outline" size="sm" onClick={() => inksQuery.refetch()}>
                  다시 시도
                </Button>
              </div>
            ) : layers.length === 0 ? (
              <div className="p-6 text-center text-gray-400 bg-white rounded-lg border border-gray-200">
                레이어를 추가하여 배합비를 작성하세요.
              </div>
            ) : (
              <div className="space-y-6">
                {layers.map(layer => (
                  <div key={layer.layer_number} className="space-y-3">
                    <div className="flex justify-end">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-gray-400 hover:text-red-500"
                        onClick={() => removeLayer(layer.layer_number)}
                      >
                        <X className="w-4 h-4 mr-1" />
                        레이어 삭제
                      </Button>
                    </div>
                    <LayerEditorWithSelector
                      layerNumber={layer.layer_number}
                      inkItems={layer.ink_items}
                      thinnerPct={layer.thinner_pct ?? undefined}
                      hardenerPct={layer.hardener_pct ?? undefined}
                      inks={inks}
                      onInksChange={items => updateLayer(layer.layer_number, { ink_items: items })}
                      onAddInk={(ink, amount) => handleAddInk(layer.layer_number, ink, amount)}
                      onThinnerChange={v => updateLayer(layer.layer_number, { thinner_pct: v })}
                      onHardenerChange={v => updateLayer(layer.layer_number, { hardener_pct: v })}
                    />
                    <RegisterBlendForm layer={layer} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <ColorPreview layers={layers} baseColor={baseSci} inks={inks} />
          </div>

          {formError && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {formError}
            </div>
          )}

          {createMutation.isError && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              샘플 저장에 실패했습니다: {getErrorMessage(createMutation.error)}
            </div>
          )}

          <div className="mt-6">
            <Button
              onClick={handleSave}
              disabled={
                createMutation.isPending ||
                !roundId ||
                layers.length === 0 ||
                layers.some(l => l.ink_items.length === 0)
              }
              className="w-full"
            >
              {createMutation.isPending ? '저장 중...' : '저장'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function NewSamplePage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-5xl mx-auto px-4 py-8 text-center text-gray-500">
          페이지를 불러오는 중...
        </div>
      }
    >
      <NewSampleForm />
    </Suspense>
  )
}
