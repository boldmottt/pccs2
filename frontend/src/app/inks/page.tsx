'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { inksApi, type InkCreateData } from '@/lib/api/inks'
import type { Ink } from '@/lib/types/project'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Plus, X, Beaker, ChevronDown } from 'lucide-react'

const INK_CATEGORIES = [
  { value: 'COLOR', label: '컬러 (COLOR)' },
  { value: 'TRANSPARENT', label: '투명 (TRANSPARENT)' },
  { value: 'EFFECT', label: '이펙트 (EFFECT)' },
  { value: 'ADDITIVE', label: '첨가제 (ADDITIVE)' },
] as const

function CategoryBadge({ category }: { category: string }) {
  const colors: Record<string, string> = {
    COLOR: 'bg-blue-50 text-blue-700 border-blue-200',
    TRANSPARENT: 'bg-gray-50 text-gray-600 border-gray-200',
    EFFECT: 'bg-purple-50 text-purple-700 border-purple-200',
    ADDITIVE: 'bg-amber-50 text-amber-700 border-amber-200',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded border ${colors[category] ?? colors.COLOR}`}>
      {category}
    </span>
  )
}

function InkCard({ ink }: { ink: Ink }) {
  const sci = ink.solidColorSci as Record<string, number> | undefined
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-gray-900 truncate pr-2">{ink.inkName}</h3>
        <CategoryBadge category={ink.inkCategory} />
      </div>
      {ink.manufacturer && (
        <p className="text-sm text-gray-500 mb-2">{ink.manufacturer}</p>
      )}
      <div className="flex items-center gap-3 text-xs text-gray-400">
        {sci && (
          <span>L*{sci.L?.toFixed(1)} a*{sci.a?.toFixed(1)} b*{sci.b?.toFixed(1)}</span>
        )}
        {ink.isBlendInk && (
          <span className="text-emerald-600 font-medium">Blend</span>
        )}
      </div>
      {ink.memo && (
        <p className="text-xs text-gray-400 mt-2 line-clamp-2">{ink.memo}</p>
      )}
    </div>
  )
}

function InkRegistrationForm({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const queryClient = useQueryClient()

  const [form, setForm] = useState<InkCreateData>({
    ink_name: '',
    ink_category: 'COLOR',
  })
  const [showColor, setShowColor] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const mutation = useMutation({
    mutationFn: (data: InkCreateData) => inksApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inks'] })
      onSuccess()
    },
  })

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}
    if (!form.ink_name.trim()) {
      newErrors.ink_name = '잉크 이름을 입력하세요'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    mutation.mutate(form)
  }

  const updateField = <K extends keyof InkCreateData>(field: K, value: InkCreateData[K]) => {
    setForm({ ...form, [field]: value })
    if (errors[field]) {
      const { [field]: _, ...rest } = errors
      setErrors(rest)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-semibold">잉크마스터 등록</h2>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <X className="w-5 h-5" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          id="ink_name"
          label="잉크 이름 *"
          placeholder="예: PMS 186C Red"
          value={form.ink_name}
          onChange={e => updateField('ink_name', e.target.value)}
          error={errors.ink_name}
          autoFocus
        />

        <div>
          <label htmlFor="ink_category" className="block text-sm font-medium text-gray-700 mb-1">
            카테고리
          </label>
          <div className="relative">
            <select
              id="ink_category"
              value={form.ink_category}
              onChange={e => updateField('ink_category', e.target.value as InkCreateData['ink_category'])}
              className="flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm appearance-none focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
            >
              {INK_CATEGORIES.map(cat => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>

        <Input
          id="manufacturer"
          label="제조사"
          placeholder="잉크 제조사"
          value={form.manufacturer ?? ''}
          onChange={e => updateField('manufacturer', e.target.value || undefined)}
        />

        <div>
          <button
            type="button"
            onClick={() => setShowColor(!showColor)}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            {showColor ? '색상 데이터 숨기기' : '색상 데이터 입력 (선택)'}
          </button>

          {showColor && (
            <div className="mt-3 space-y-3 p-4 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 font-medium">SCI 측정값 (L*, a*, b*)</p>
              <div className="grid grid-cols-3 gap-3">
                <Input
                  id="sci_L"
                  label="L*"
                  type="number"
                  step="0.01"
                  placeholder="0~100"
                  value={form.solid_color_sci?.L ?? ''}
                  onChange={e => {
                    const val = e.target.value ? Number(e.target.value) : undefined
                    const prev = form.solid_color_sci ?? { L: 0, a: 0, b: 0 }
                    updateField('solid_color_sci', val !== undefined ? { ...prev, L: val } : undefined)
                  }}
                />
                <Input
                  id="sci_a"
                  label="a*"
                  type="number"
                  step="0.01"
                  placeholder="-128~127"
                  value={form.solid_color_sci?.a ?? ''}
                  onChange={e => {
                    const val = e.target.value ? Number(e.target.value) : undefined
                    const prev = form.solid_color_sci ?? { L: 0, a: 0, b: 0 }
                    updateField('solid_color_sci', val !== undefined ? { ...prev, a: val } : undefined)
                  }}
                />
                <Input
                  id="sci_b"
                  label="b*"
                  type="number"
                  step="0.01"
                  placeholder="-128~127"
                  value={form.solid_color_sci?.b ?? ''}
                  onChange={e => {
                    const val = e.target.value ? Number(e.target.value) : undefined
                    const prev = form.solid_color_sci ?? { L: 0, a: 0, b: 0 }
                    updateField('solid_color_sci', val !== undefined ? { ...prev, b: val } : undefined)
                  }}
                />
              </div>

              <p className="text-xs text-gray-500 font-medium mt-3">SCE 측정값 (L*, a*, b*)</p>
              <div className="grid grid-cols-3 gap-3">
                <Input
                  id="sce_L"
                  label="L*"
                  type="number"
                  step="0.01"
                  value={form.solid_color_sce?.L ?? ''}
                  onChange={e => {
                    const val = e.target.value ? Number(e.target.value) : undefined
                    const prev = form.solid_color_sce ?? { L: 0, a: 0, b: 0 }
                    updateField('solid_color_sce', val !== undefined ? { ...prev, L: val } : undefined)
                  }}
                />
                <Input
                  id="sce_a"
                  label="a*"
                  type="number"
                  step="0.01"
                  value={form.solid_color_sce?.a ?? ''}
                  onChange={e => {
                    const val = e.target.value ? Number(e.target.value) : undefined
                    const prev = form.solid_color_sce ?? { L: 0, a: 0, b: 0 }
                    updateField('solid_color_sce', val !== undefined ? { ...prev, a: val } : undefined)
                  }}
                />
                <Input
                  id="sce_b"
                  label="b*"
                  type="number"
                  step="0.01"
                  value={form.solid_color_sce?.b ?? ''}
                  onChange={e => {
                    const val = e.target.value ? Number(e.target.value) : undefined
                    const prev = form.solid_color_sce ?? { L: 0, a: 0, b: 0 }
                    updateField('solid_color_sce', val !== undefined ? { ...prev, b: val } : undefined)
                  }}
                />
              </div>

              <div className="grid grid-cols-3 gap-3 mt-3">
                <Input
                  id="gloss_GU"
                  label="광택 (GU)"
                  type="number"
                  step="0.1"
                  value={form.gloss_GU ?? ''}
                  onChange={e => updateField('gloss_GU', e.target.value ? Number(e.target.value) : undefined)}
                />
                <Input
                  id="viscosity"
                  label="점도"
                  type="number"
                  step="0.1"
                  value={form.viscosity ?? ''}
                  onChange={e => updateField('viscosity', e.target.value ? Number(e.target.value) : undefined)}
                />
                <Input
                  id="density"
                  label="밀도"
                  type="number"
                  step="0.01"
                  value={form.density ?? ''}
                  onChange={e => updateField('density', e.target.value ? Number(e.target.value) : undefined)}
                />
              </div>
            </div>
          )}
        </div>

        <div>
          <label htmlFor="memo" className="block text-sm font-medium text-gray-700 mb-1">
            메모
          </label>
          <textarea
            id="memo"
            rows={2}
            placeholder="잉크 관련 메모"
            value={form.memo ?? ''}
            onChange={e => updateField('memo', e.target.value || undefined)}
            className="flex w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent resize-none"
          />
        </div>

        {mutation.isError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            잉크 등록에 실패했습니다. 다시 시도해주세요.
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <Button variant="outline" type="button" onClick={onClose}>
            취소
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? '등록 중...' : '잉크마스터 등록'}
          </Button>
        </div>
      </form>
    </div>
  )
}

export default function InksPage() {
  const [showForm, setShowForm] = useState(false)
  const [filterCategory, setFilterCategory] = useState<string>('')

  const { data: inks, isLoading } = useQuery({
    queryKey: ['inks', filterCategory],
    queryFn: () => inksApi.getAll(filterCategory ? { category: filterCategory } : undefined),
  })

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Inks</h1>
          <p className="text-gray-600 mt-1">잉크 마스터 데이터</p>
        </div>
        {!showForm && (
          <Button onClick={() => setShowForm(true)}>
            <Plus className="w-4 h-4 mr-2" />
            잉크마스터 등록
          </Button>
        )}
      </div>

      {showForm && (
        <div className="mb-6">
          <InkRegistrationForm
            onClose={() => setShowForm(false)}
            onSuccess={() => setShowForm(false)}
          />
        </div>
      )}

      <div className="flex items-center gap-2 mb-4">
        <button
          onClick={() => setFilterCategory('')}
          className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
            !filterCategory ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
          }`}
        >
          전체
        </button>
        {INK_CATEGORIES.map(cat => (
          <button
            key={cat.value}
            onClick={() => setFilterCategory(cat.value)}
            className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
              filterCategory === cat.value ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="p-8 text-center text-gray-500">Loading inks...</div>
      ) : inks && inks.length > 0 ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {inks.map(ink => (
            <InkCard key={ink.inkId} ink={ink} />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <Beaker className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">등록된 잉크가 없습니다.</p>
          <p className="text-sm text-gray-400 mt-1">잉크마스터를 등록하여 시작하세요.</p>
        </div>
      )}
    </div>
  )
}
