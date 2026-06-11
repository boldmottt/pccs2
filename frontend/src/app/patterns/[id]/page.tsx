'use client'

import { use, useState } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { patternsApi } from '@/lib/api/patterns'
import { roundsApi } from '@/lib/api/rounds'
import { samplesApi } from '@/lib/api/samples'
import { getErrorMessage } from '@/lib/api/client'
import type { Pattern, Round, Sample } from '@/lib/types/project'
import { labToCss } from '@/lib/types/color'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { ColorTrendChart, type DataPoint } from '@/components/visualization/ColorTrendChart'
import { SuccessFlagBadge } from '@/components/samples/SuccessFlagBadge'
import { ArrowLeft, Pencil, Plus, X } from 'lucide-react'

const PATTERN_STATUS_LABEL: Record<Pattern['status'], string> = {
  DEVELOPING: '개발 중',
  COMPLETED: '완료',
  ON_HOLD: '보류',
}

const PATTERN_STATUS_STYLE: Record<Pattern['status'], string> = {
  DEVELOPING: 'bg-blue-100 text-blue-800 border-blue-200',
  COMPLETED: 'bg-green-100 text-green-800 border-green-200',
  ON_HOLD: 'bg-gray-100 text-gray-800 border-gray-200',
}

function RoundCard({ round }: { round: Round }) {
  const samplesQuery = useQuery({
    queryKey: ['samples', { round_id: round.round_id }],
    queryFn: () => samplesApi.list({ round_id: round.round_id }),
  })

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>라운드 {round.round_number}</CardTitle>
          <div className="flex items-center gap-3">
            {round.work_date && <span className="text-sm text-gray-500">{round.work_date}</span>}
            <Link href={`/samples/new?round_id=${round.round_id}`}>
              <Button variant="outline" size="sm">
                <Plus className="w-4 h-4 mr-1" />
                샘플 추가
              </Button>
            </Link>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {samplesQuery.isLoading ? (
          <p className="text-sm text-gray-500">샘플을 불러오는 중...</p>
        ) : samplesQuery.isError ? (
          <div className="text-sm">
            <p className="text-red-600 mb-2">{getErrorMessage(samplesQuery.error)}</p>
            <Button variant="outline" size="sm" onClick={() => samplesQuery.refetch()}>
              다시 시도
            </Button>
          </div>
        ) : samplesQuery.data && samplesQuery.data.length > 0 ? (
          <div className="divide-y divide-gray-100">
            {samplesQuery.data.map(sample => (
              <Link
                key={sample.sample_id}
                href={`/samples/${sample.sample_id}`}
                className="flex items-center justify-between py-2 hover:bg-gray-50 px-2 -mx-2 rounded-lg transition-colors"
              >
                <span className="font-medium text-sm">샘플 {sample.sample_number}</span>
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-gray-500">
                    ΔE:{' '}
                    {sample.final_delta_e !== null && sample.final_delta_e !== undefined
                      ? sample.final_delta_e.toFixed(2)
                      : '-'}
                  </span>
                  <SuccessFlagBadge flag={sample.success_flag} />
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">샘플이 없습니다.</p>
        )}
      </CardContent>
    </Card>
  )
}

function EditPatternForm({ pattern, onClose }: { pattern: Pattern; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [patternName, setPatternName] = useState(pattern.pattern_name)
  const [totalLayers, setTotalLayers] = useState(String(pattern.total_print_layers))
  const [status, setStatus] = useState<Pattern['status']>(pattern.status)
  const [baseMaterial, setBaseMaterial] = useState(pattern.target_base_material ?? '')
  const [sci, setSci] = useState(pattern.target_base_color_sci ?? { L: 0, a: 0, b: 0 })
  const [hasSci] = useState(!!pattern.target_base_color_sci)
  const [notes, setNotes] = useState(pattern.notes ?? '')
  const [nameError, setNameError] = useState<string | undefined>()

  const mutation = useMutation({
    mutationFn: () =>
      patternsApi.update(pattern.pattern_id, {
        pattern_name: patternName.trim(),
        total_print_layers: Math.max(1, Number(totalLayers) || 1),
        status,
        target_base_material: baseMaterial.trim() || undefined,
        ...(hasSci ? { target_base_color_sci: sci } : {}),
        notes: notes.trim() || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patterns'] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!patternName.trim()) {
      setNameError('패턴 이름을 입력하세요')
      return
    }
    mutation.mutate()
  }

  return (
    <Card className="mb-8">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>패턴 수정</CardTitle>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid sm:grid-cols-3 gap-4">
            <Input
              label="패턴 이름 *"
              value={patternName}
              onChange={e => {
                setPatternName(e.target.value)
                setNameError(undefined)
              }}
              error={nameError}
            />
            <Input
              label="총 인쇄 도수"
              type="number"
              min="1"
              value={totalLayers}
              onChange={e => setTotalLayers(e.target.value)}
            />
            <div>
              <label htmlFor="pattern_status" className="block text-sm font-medium text-gray-700 mb-1">
                상태
              </label>
              <select
                id="pattern_status"
                value={status}
                onChange={e => setStatus(e.target.value as Pattern['status'])}
                className="flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
              >
                {(Object.keys(PATTERN_STATUS_LABEL) as Pattern['status'][]).map(value => (
                  <option key={value} value={value}>
                    {PATTERN_STATUS_LABEL[value]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {hasSci && (
            <div>
              <p className="text-xs text-gray-500 font-medium mb-2">목표 색상 SCI (L*, a*, b*)</p>
              <div className="grid grid-cols-3 gap-3">
                {(['L', 'a', 'b'] as const).map(key => (
                  <Input
                    key={key}
                    label={`${key}*`}
                    type="number"
                    step="0.01"
                    value={sci[key]}
                    onChange={e => setSci({ ...sci, [key]: Number(e.target.value) || 0 })}
                  />
                ))}
              </div>
            </div>
          )}

          <Input
            label="목표 베이스 소재"
            value={baseMaterial}
            onChange={e => setBaseMaterial(e.target.value)}
          />

          <div>
            <label htmlFor="pattern_notes" className="block text-sm font-medium text-gray-700 mb-1">
              메모
            </label>
            <textarea
              id="pattern_notes"
              rows={2}
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className="flex w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent resize-none"
            />
          </div>

          {mutation.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              패턴 수정에 실패했습니다: {getErrorMessage(mutation.error)}
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

export default function PatternDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const queryClient = useQueryClient()
  const [editingPattern, setEditingPattern] = useState(false)

  const patternQuery = useQuery({
    queryKey: ['patterns', 'detail', id],
    queryFn: () => patternsApi.get(id),
  })

  const roundsQuery = useQuery({
    queryKey: ['rounds', id],
    queryFn: () => roundsApi.list({ pattern_id: id }),
  })

  const patternSamplesQuery = useQuery({
    queryKey: ['samples', { pattern_id: id }],
    queryFn: () => samplesApi.list({ pattern_id: id }),
  })

  const createRoundMutation = useMutation({
    mutationFn: () => roundsApi.create(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rounds', id] })
    },
  })

  const pattern = patternQuery.data

  const trendSamples = (patternSamplesQuery.data ?? [])
    .filter(
      (s: Sample) => s.final_delta_e !== null && s.final_delta_e !== undefined,
    )
    .sort((a, b) => a.sample_number - b.sample_number)

  const trendData: DataPoint[] = trendSamples.map(sample => {
    const lastLayerColor = [...sample.layers].reverse().find(l => l.print_color_sci)?.print_color_sci
    const color = lastLayerColor ?? sample.base_color_sci
    return {
      round: `샘플 ${sample.sample_number}`,
      L: color.L,
      a: color.a,
      b: color.b,
      deltaE: sample.final_delta_e ?? undefined,
    }
  })

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {pattern ? (
        <Link
          href={`/projects/${pattern.project_id}`}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 mb-6 transition-colors w-fit"
        >
          <ArrowLeft className="w-4 h-4" />
          프로젝트 상세
        </Link>
      ) : (
        <Link
          href="/projects"
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 mb-6 transition-colors w-fit"
        >
          <ArrowLeft className="w-4 h-4" />
          프로젝트 목록
        </Link>
      )}

      {patternQuery.isLoading ? (
        <div className="p-8 text-center text-gray-500 bg-white rounded-lg border border-gray-200">
          패턴을 불러오는 중...
        </div>
      ) : patternQuery.isError ? (
        <div className="p-8 text-center bg-white rounded-lg border border-gray-200">
          <p className="text-red-600 mb-4">{getErrorMessage(patternQuery.error)}</p>
          <Button variant="outline" onClick={() => patternQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      ) : pattern ? (
        editingPattern ? (
          <EditPatternForm pattern={pattern} onClose={() => setEditingPattern(false)} />
        ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              {pattern.target_base_color_sci && (
                <div className="flex flex-col items-center gap-1">
                  <div
                    className="w-16 h-16 rounded-lg border border-gray-200 shadow-md"
                    style={{ backgroundColor: labToCss(pattern.target_base_color_sci) }}
                  />
                  <span className="text-xs text-gray-500">목표 색상</span>
                </div>
              )}
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{pattern.pattern_name}</h1>
                <p className="text-gray-600 mt-1">
                  {pattern.total_print_layers}도 인쇄
                  {pattern.target_base_material ? ` · ${pattern.target_base_material}` : ''}
                </p>
                {pattern.target_base_color_sci && (
                  <p className="text-sm text-gray-500 mt-1">
                    목표 SCI: L* {pattern.target_base_color_sci.L.toFixed(1)}, a*{' '}
                    {pattern.target_base_color_sci.a.toFixed(1)}, b*{' '}
                    {pattern.target_base_color_sci.b.toFixed(1)}
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`px-3 py-1 rounded-full text-xs font-medium border ${PATTERN_STATUS_STYLE[pattern.status]}`}
              >
                {PATTERN_STATUS_LABEL[pattern.status]}
              </span>
              <Button variant="outline" size="sm" onClick={() => setEditingPattern(true)}>
                <Pencil className="w-3.5 h-3.5 mr-1" />
                수정
              </Button>
            </div>
          </div>
        </div>
        )
      ) : null}

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">라운드</h2>
        <Button onClick={() => createRoundMutation.mutate()} disabled={createRoundMutation.isPending}>
          <Plus className="w-4 h-4 mr-1" />
          {createRoundMutation.isPending ? '생성 중...' : '새 라운드'}
        </Button>
      </div>

      {createRoundMutation.isError && (
        <div className="p-3 mb-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          라운드 생성에 실패했습니다: {getErrorMessage(createRoundMutation.error)}
        </div>
      )}

      {roundsQuery.isLoading ? (
        <div className="p-8 text-center text-gray-500 bg-white rounded-lg border border-gray-200">
          라운드를 불러오는 중...
        </div>
      ) : roundsQuery.isError ? (
        <div className="p-8 text-center bg-white rounded-lg border border-gray-200">
          <p className="text-red-600 mb-4">{getErrorMessage(roundsQuery.error)}</p>
          <Button variant="outline" onClick={() => roundsQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      ) : roundsQuery.data && roundsQuery.data.length > 0 ? (
        <div className="space-y-4">
          {roundsQuery.data.map(round => (
            <RoundCard key={round.round_id} round={round} />
          ))}
        </div>
      ) : (
        <div className="p-8 text-center text-gray-500 bg-white rounded-lg border border-gray-200">
          라운드가 없습니다. 새 라운드를 생성하세요.
        </div>
      )}

      {patternSamplesQuery.isLoading ? (
        <div className="mt-8 p-4 text-center text-sm text-gray-500 bg-white rounded-lg border border-gray-200">
          색상 추이 데이터를 불러오는 중...
        </div>
      ) : patternSamplesQuery.isError ? (
        <div className="mt-8 p-4 text-center bg-white rounded-lg border border-gray-200">
          <p className="text-sm text-red-600 mb-2">{getErrorMessage(patternSamplesQuery.error)}</p>
          <Button variant="outline" size="sm" onClick={() => patternSamplesQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      ) : trendData.length > 0 ? (
        <div className="mt-8">
          <ColorTrendChart
            dataPoints={trendData}
            targetColor={pattern?.target_base_color_sci ?? undefined}
          />
        </div>
      ) : null}
    </div>
  )
}
