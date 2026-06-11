'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { basesApi } from '@/lib/api/bases'
import { getErrorMessage } from '@/lib/api/client'
import type { BaseMaster, BaseMasterCreate, Lab } from '@/lib/types/project'
import { labToCss } from '@/lib/types/color'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Plus, X, Square, Pencil } from 'lucide-react'

function LabFields({
  label,
  value,
  onChange,
}: {
  label: string
  value?: Lab
  onChange: (value: Lab | undefined) => void
}) {
  const update = (key: keyof Lab, raw: string) => {
    const num = raw === '' ? undefined : Number(raw)
    const prev = value ?? { L: 0, a: 0, b: 0 }
    if (num === undefined && raw === '') {
      onChange({ ...prev, [key]: 0 })
      return
    }
    onChange({ ...prev, [key]: num ?? 0 })
  }
  return (
    <div>
      <p className="text-xs text-gray-500 font-medium mb-2">{label}</p>
      <div className="grid grid-cols-3 gap-3">
        <Input label="L*" type="number" step="0.01" value={value?.L ?? ''} onChange={e => update('L', e.target.value)} />
        <Input label="a*" type="number" step="0.01" value={value?.a ?? ''} onChange={e => update('a', e.target.value)} />
        <Input label="b*" type="number" step="0.01" value={value?.b ?? ''} onChange={e => update('b', e.target.value)} />
      </div>
    </div>
  )
}

function BaseForm({
  base,
  onClose,
}: {
  base?: BaseMaster
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<BaseMasterCreate>(
    base
      ? {
          base_code: base.base_code,
          base_name: base.base_name ?? undefined,
          material: base.material ?? undefined,
          color_sci: base.color_sci ?? undefined,
          color_sce: base.color_sce ?? undefined,
          maker: base.maker ?? undefined,
          memo: base.memo ?? undefined,
        }
      : { base_code: '' },
  )
  const [codeError, setCodeError] = useState<string | undefined>()

  const mutation = useMutation({
    mutationFn: () => (base ? basesApi.update(base.base_id, form) : basesApi.create(form)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bases'] })
      onClose()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => basesApi.remove(base!.base_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bases'] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.base_code.trim()) {
      setCodeError('베이스 코드를 입력하세요')
      return
    }
    mutation.mutate()
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-semibold">
          {base ? `베이스 수정 — ${base.base_code}` : '베이스 마스터 등록'}
        </h2>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <X className="w-5 h-5" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid sm:grid-cols-3 gap-4">
          <Input
            label="베이스 코드 *"
            placeholder="예: K-1116S"
            value={form.base_code}
            onChange={e => {
              setForm({ ...form, base_code: e.target.value })
              setCodeError(undefined)
            }}
            error={codeError}
            autoFocus={!base}
          />
          <Input
            label="이름"
            placeholder="예: 새틀 패턴 도장"
            value={form.base_name ?? ''}
            onChange={e => setForm({ ...form, base_name: e.target.value || undefined })}
          />
          <Input
            label="소재"
            placeholder="예: ABS"
            value={form.material ?? ''}
            onChange={e => setForm({ ...form, material: e.target.value || undefined })}
          />
        </div>

        <LabFields label="측색값 SCI (L*, a*, b*)" value={form.color_sci} onChange={v => setForm({ ...form, color_sci: v })} />
        <LabFields label="측색값 SCE (L*, a*, b*)" value={form.color_sce} onChange={v => setForm({ ...form, color_sce: v })} />

        <div className="grid sm:grid-cols-2 gap-4">
          <Input
            label="도장 메이커"
            placeholder="예: HT-77"
            value={form.maker ?? ''}
            onChange={e => setForm({ ...form, maker: e.target.value || undefined })}
          />
          <Input
            label="메모"
            value={form.memo ?? ''}
            onChange={e => setForm({ ...form, memo: e.target.value || undefined })}
          />
        </div>

        {mutation.isError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            저장에 실패했습니다: {getErrorMessage(mutation.error)}
          </div>
        )}
        {deleteMutation.isError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            삭제에 실패했습니다: {getErrorMessage(deleteMutation.error)}
          </div>
        )}

        <div className="flex justify-between gap-3 pt-2">
          {base ? (
            <Button
              variant="outline"
              type="button"
              onClick={() => {
                if (window.confirm(`베이스 "${base.base_code}"을(를) 삭제할까요?`)) {
                  deleteMutation.mutate()
                }
              }}
              disabled={deleteMutation.isPending}
              className="text-red-600 border-red-200 hover:bg-red-50"
            >
              {deleteMutation.isPending ? '삭제 중...' : '삭제'}
            </Button>
          ) : (
            <span />
          )}
          <div className="flex gap-3">
            <Button variant="outline" type="button" onClick={onClose}>
              취소
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? '저장 중...' : base ? '저장' : '등록'}
            </Button>
          </div>
        </div>
      </form>
    </div>
  )
}

export default function BasesPage() {
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<BaseMaster | null>(null)
  const [search, setSearch] = useState('')

  const { data: bases, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['bases'],
    queryFn: () => basesApi.list(),
  })

  const filtered = (bases ?? []).filter(
    b =>
      !search ||
      b.base_code.toLowerCase().includes(search.toLowerCase()) ||
      (b.base_name ?? '').toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">베이스</h1>
          <p className="text-gray-600 mt-1">베이스(소재·도장) 마스터 데이터 — 코드로 측색값 불러오기</p>
        </div>
        {!showForm && !editing && (
          <Button onClick={() => setShowForm(true)}>
            <Plus className="w-4 h-4 mr-2" />
            베이스 등록
          </Button>
        )}
      </div>

      {showForm && (
        <div className="mb-6">
          <BaseForm onClose={() => setShowForm(false)} />
        </div>
      )}
      {editing && (
        <div className="mb-6">
          <BaseForm key={editing.base_id} base={editing} onClose={() => setEditing(null)} />
        </div>
      )}

      <div className="mb-4 max-w-xs">
        <Input
          placeholder="코드/이름 검색"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {isLoading ? (
        <div className="p-8 text-center text-gray-500">베이스를 불러오는 중...</div>
      ) : isError ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <p className="text-red-600 mb-4">{getErrorMessage(error)}</p>
          <Button variant="outline" onClick={() => refetch()}>
            다시 시도
          </Button>
        </div>
      ) : filtered.length > 0 ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map(base => (
            <div
              key={base.base_id}
              className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-sm transition-shadow group relative"
            >
              <button
                type="button"
                onClick={() => {
                  setShowForm(false)
                  setEditing(base)
                  window.scrollTo({ top: 0, behavior: 'smooth' })
                }}
                title="베이스 수정"
                className="absolute right-3 bottom-3 p-1.5 rounded-md text-gray-300 hover:text-primary-600 hover:bg-primary-50 group-hover:text-gray-400 transition-colors"
              >
                <Pencil className="w-4 h-4" />
              </button>
              <div className="flex items-start gap-3">
                {base.color_sci ? (
                  <div
                    className="w-10 h-10 rounded-lg border border-gray-200 shrink-0"
                    style={{ backgroundColor: labToCss(base.color_sci) }}
                  />
                ) : (
                  <div className="w-10 h-10 rounded-lg border border-dashed border-gray-300 shrink-0 flex items-center justify-center">
                    <Square className="w-4 h-4 text-gray-300" />
                  </div>
                )}
                <div className="min-w-0">
                  <h3 className="font-semibold text-gray-900 truncate">{base.base_code}</h3>
                  <p className="text-sm text-gray-500 truncate">
                    {base.base_name || '-'}
                    {base.material ? ` · ${base.material}` : ''}
                  </p>
                  {base.color_sci && (
                    <p className="text-xs text-gray-400 mt-1">
                      L*{base.color_sci.L.toFixed(1)} a*{base.color_sci.a.toFixed(1)} b*
                      {base.color_sci.b.toFixed(1)}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <Square className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">등록된 베이스가 없습니다.</p>
          <p className="text-sm text-gray-400 mt-1">
            자주 쓰는 베이스 코드를 등록해 두면 샘플 작성 시 코드만으로 색상을 불러올 수 있습니다.
          </p>
        </div>
      )}
    </div>
  )
}
