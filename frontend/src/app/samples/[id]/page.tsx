'use client'

import { use, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { samplesApi } from '@/lib/api/samples'
import { patternsApi } from '@/lib/api/patterns'
import { inksApi } from '@/lib/api/inks'
import { getErrorMessage } from '@/lib/api/client'
import type { Layer, Sample, SuccessFlag } from '@/lib/types/project'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { ColorSwatch } from '@/components/color/ColorSwatch'
import { ColorComparison } from '@/components/color/ColorComparison'
import { SuccessFlagBadge } from '@/components/samples/SuccessFlagBadge'
import { InkDonutChart, type InkData } from '@/components/visualization/InkDonutChart'
import { labToCss } from '@/lib/types/color'
import { ArrowLeft, Pencil, Trash2, X } from 'lucide-react'

const SUCCESS_FLAG_LABEL: Record<SuccessFlag, string> = {
  SUCCESS: '성공',
  FAILED: '실패',
  PENDING: '대기',
}

function EditSampleForm({ sample, onClose }: { sample: Sample; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [baseMaterial, setBaseMaterial] = useState(sample.base_material)
  const [sci, setSci] = useState({ ...sample.base_color_sci })
  const [sce, setSce] = useState({ ...sample.base_color_sce })
  const [successFlag, setSuccessFlag] = useState<SuccessFlag>(sample.success_flag)
  const [successNotes, setSuccessNotes] = useState(sample.success_notes ?? '')

  const mutation = useMutation({
    mutationFn: () =>
      samplesApi.update(sample.sample_id, {
        base_material: baseMaterial.trim() || sample.base_material,
        base_color_sci: sci,
        base_color_sce: sce,
        success_flag: successFlag,
        success_notes: successNotes.trim() || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples'] })
      onClose()
    },
  })

  const labInputs = (
    label: string,
    value: { L: number; a: number; b: number },
    onChange: (v: { L: number; a: number; b: number }) => void,
  ) => (
    <div>
      <p className="text-xs text-gray-500 font-medium mb-2">{label}</p>
      <div className="grid grid-cols-3 gap-3">
        {(['L', 'a', 'b'] as const).map(key => (
          <Input
            key={key}
            label={`${key}*`}
            type="number"
            step="0.01"
            value={value[key]}
            onChange={e => onChange({ ...value, [key]: Number(e.target.value) || 0 })}
          />
        ))}
      </div>
    </div>
  )

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>샘플 {sample.sample_number} 수정</CardTitle>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <form
          onSubmit={e => {
            e.preventDefault()
            mutation.mutate()
          }}
          className="space-y-4"
        >
          <div className="grid sm:grid-cols-2 gap-4">
            <Input
              label="베이스 소재"
              value={baseMaterial}
              onChange={e => setBaseMaterial(e.target.value)}
            />
            <div>
              <label htmlFor="success_flag" className="block text-sm font-medium text-gray-700 mb-1">
                결과
              </label>
              <select
                id="success_flag"
                value={successFlag}
                onChange={e => setSuccessFlag(e.target.value as SuccessFlag)}
                className="flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
              >
                {(Object.keys(SUCCESS_FLAG_LABEL) as SuccessFlag[]).map(value => (
                  <option key={value} value={value}>
                    {SUCCESS_FLAG_LABEL[value]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {labInputs('베이스 색상 SCI (L*, a*, b*)', sci, setSci)}
          {labInputs('베이스 색상 SCE (L*, a*, b*)', sce, setSce)}

          <div>
            <label htmlFor="success_notes" className="block text-sm font-medium text-gray-700 mb-1">
              결과 메모
            </label>
            <textarea
              id="success_notes"
              rows={2}
              value={successNotes}
              onChange={e => setSuccessNotes(e.target.value)}
              className="flex w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent resize-none"
            />
          </div>

          {mutation.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              샘플 수정에 실패했습니다: {getErrorMessage(mutation.error)}
            </div>
          )}

          <div className="flex justify-end gap-3">
            <Button variant="outline" type="button" onClick={onClose}>
              취소
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? '저장 중...' : '저장'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

function LayerCard({
  layer,
  inkName,
  inkColor,
}: {
  layer: Layer
  inkName: (inkId: string) => string
  inkColor: (inkId: string) => string
}) {
  const totalAmount = layer.ink_items.reduce((sum, item) => sum + item.amount, 0)

  const donutInks: InkData[] = layer.ink_items.map(item => ({
    inkId: item.ink_id,
    inkName: inkName(item.ink_id),
    amount: item.amount,
    color: inkColor(item.ink_id),
  }))

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>{layer.layer_number}도</CardTitle>
          <span className="text-sm text-gray-500">총량: {totalAmount.toFixed(1)}g</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-5">
          {totalAmount > 0 && (
            <div className="shrink-0">
              <InkDonutChart inks={donutInks} totalAmount={totalAmount} size="sm" showLabels={false} />
            </div>
          )}
          <div className="flex-1 space-y-2">
            {layer.ink_items.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-sm">
                <span className="flex items-center gap-2 font-medium">
                  <span
                    className="w-3 h-3 rounded-full border border-gray-200 shrink-0"
                    style={{ backgroundColor: donutInks[index]?.color }}
                  />
                  {inkName(item.ink_id)}
                </span>
                <span className="text-gray-500">
                  {item.amount.toFixed(1)}g
                  {totalAmount > 0 ? ` (${((item.amount / totalAmount) * 100).toFixed(0)}%)` : ''}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          {layer.thinner_pct !== null && layer.thinner_pct !== undefined && (
            <span>신너: {layer.thinner_pct}%</span>
          )}
          {layer.hardener_pct !== null && layer.hardener_pct !== undefined && (
            <span>경화제: {layer.hardener_pct}%</span>
          )}
          {layer.delta_E_from_target !== null && layer.delta_E_from_target !== undefined && (
            <span>목표 대비 ΔE: {layer.delta_E_from_target.toFixed(2)}</span>
          )}
        </div>

        {(layer.print_color_sci || layer.print_color_sce) && (
          <div className="flex items-center gap-6 pt-2 border-t border-gray-100">
            {layer.print_color_sci && (
              <ColorSwatch color={layer.print_color_sci} label="인쇄 색상 SCI" size="md" />
            )}
            {layer.print_color_sce && (
              <ColorSwatch color={layer.print_color_sce} label="인쇄 색상 SCE" size="md" />
            )}
          </div>
        )}

        {layer.note && <p className="text-sm text-gray-500">{layer.note}</p>}
      </CardContent>
    </Card>
  )
}

export default function SampleDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)

  const deleteMutation = useMutation({
    mutationFn: () => samplesApi.remove(id),
  })

  const handleDelete = (patternId?: string) => {
    if (window.confirm('이 샘플을 삭제할까요?')) {
      deleteMutation.mutate(undefined, {
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['samples'] })
          router.push(patternId ? `/patterns/${patternId}` : '/samples')
        },
      })
    }
  }

  const sampleQuery = useQuery({
    queryKey: ['samples', 'detail', id],
    queryFn: () => samplesApi.get(id),
  })

  const sample = sampleQuery.data

  const patternQuery = useQuery({
    queryKey: ['patterns', 'detail', sample?.pattern_id],
    queryFn: () => patternsApi.get(sample!.pattern_id),
    enabled: !!sample,
  })

  const inksQuery = useQuery({
    queryKey: ['inks'],
    queryFn: () => inksApi.list(),
  })

  const inkName = (inkId: string) =>
    inksQuery.data?.find(i => i.ink_id === inkId)?.ink_name || inkId

  // 측색값이 있으면 실제 잉크 색, 없으면 잉크 ID 기반 고정 팔레트 색
  const inkColor = (inkId: string) => {
    const sci = inksQuery.data?.find(i => i.ink_id === inkId)?.solid_color_sci
    if (sci) return labToCss(sci)
    const palette = [
      '#EF4444', '#F97316', '#F59E0B', '#84CC16',
      '#10B981', '#06B6D4', '#3B82F6', '#6366F1',
      '#8B5CF6', '#EC4899', '#F43F5E', '#A8A29E',
    ]
    let hash = 0
    for (let i = 0; i < inkId.length; i++) {
      hash = inkId.charCodeAt(i) + ((hash << 5) - hash)
    }
    return palette[Math.abs(hash) % palette.length]
  }

  if (sampleQuery.isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="p-8 text-center text-gray-500 bg-white rounded-lg border border-gray-200">
          샘플을 불러오는 중...
        </div>
      </div>
    )
  }

  if (sampleQuery.isError || !sample) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="p-8 text-center bg-white rounded-lg border border-gray-200">
          <p className="text-red-600 mb-4">{getErrorMessage(sampleQuery.error)}</p>
          <Button variant="outline" onClick={() => sampleQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      </div>
    )
  }

  const finalPrintColor = [...sample.layers]
    .reverse()
    .find(l => l.print_color_sci)?.print_color_sci

  const targetColor = patternQuery.data?.target_base_color_sci

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <Link
        href={`/patterns/${sample.pattern_id}`}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 mb-6 transition-colors w-fit"
      >
        <ArrowLeft className="w-4 h-4" />
        패턴 상세
      </Link>

      {editing && <EditSampleForm sample={sample} onClose={() => setEditing(false)} />}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold">샘플 {sample.sample_number}</h1>
            <p className="text-gray-600 mt-1">베이스 소재: {sample.base_material}</p>
          </div>
          <div className="flex items-center gap-3">
            {sample.final_delta_e !== null && sample.final_delta_e !== undefined && (
              <span className="text-sm text-gray-600">
                최종 ΔE: <strong>{sample.final_delta_e.toFixed(2)}</strong>
              </span>
            )}
            <SuccessFlagBadge flag={sample.success_flag} />
            {!editing && (
              <>
                <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                  <Pencil className="w-3.5 h-3.5 mr-1" />
                  수정
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDelete(sample.pattern_id)}
                  disabled={deleteMutation.isPending}
                  className="text-red-600 border-red-200 hover:bg-red-50"
                >
                  <Trash2 className="w-3.5 h-3.5 mr-1" />
                  삭제
                </Button>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-6">
          <ColorSwatch color={sample.base_color_sci} label="베이스 SCI" size="lg" />
          <ColorSwatch color={sample.base_color_sce} label="베이스 SCE" size="lg" />
        </div>

        {sample.success_notes && (
          <p className="text-sm text-gray-500 mt-4">{sample.success_notes}</p>
        )}
      </div>

      {targetColor && finalPrintColor && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">목표 색상 비교</h2>
          <ColorComparison
            color1={targetColor}
            color2={finalPrintColor}
            label1="목표 색상"
            label2="최종 인쇄 색상"
            deltaE={sample.final_delta_e ?? undefined}
          />
        </div>
      )}

      {patternQuery.isLoading && (
        <div className="p-4 mb-6 text-center text-sm text-gray-500 bg-white rounded-lg border border-gray-200">
          패턴 정보를 불러오는 중...
        </div>
      )}
      {patternQuery.isError && (
        <div className="p-4 mb-6 text-center bg-white rounded-lg border border-gray-200">
          <p className="text-sm text-red-600 mb-2">{getErrorMessage(patternQuery.error)}</p>
          <Button variant="outline" size="sm" onClick={() => patternQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      )}

      <h2 className="text-xl font-semibold mb-4">레이어</h2>
      {inksQuery.isLoading && (
        <p className="text-sm text-gray-500 mb-3">잉크 이름을 불러오는 중...</p>
      )}
      {inksQuery.isError && (
        <div className="mb-3 text-sm">
          <span className="text-red-600 mr-2">{getErrorMessage(inksQuery.error)}</span>
          <Button variant="outline" size="sm" onClick={() => inksQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      )}
      <div className="space-y-4">
        {sample.layers.map(layer => (
          <LayerCard key={layer.layer_number} layer={layer} inkName={inkName} inkColor={inkColor} />
        ))}
      </div>
    </div>
  )
}
