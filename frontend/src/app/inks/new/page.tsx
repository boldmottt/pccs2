'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { inksApi } from '@/lib/api/inks'
import { Button } from '@/components/ui/Button'

type FormData = {
  inkName: string
  inkCategory: 'COLOR' | 'TRANSPARENT' | 'EFFECT' | 'ADDITIVE'
  manufacturer: string
  solidColorSci: { L: number; a: number; b: number }
  solidColorSce: { L: number; a: number; b: number }
  memo: string
}

export default function NewInkPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<FormData>({
    inkName: '',
    inkCategory: 'COLOR',
    manufacturer: '',
    solidColorSci: { L: 0, a: 0, b: 0 },
    solidColorSce: { L: 0, a: 0, b: 0 },
    memo: '',
  })

  const mutation = useMutation({
    mutationFn: inksApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inks'] })
      router.push('/inks')
    },
    onError: (error: Error) => {
      console.error('Failed to create ink:', error)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">새 잉크</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">잉크명 *</label>
          <input
            type="text"
            required
            value={formData.inkName}
            onChange={e => setFormData(prev => ({ ...prev, inkName: e.target.value }))}
            className="w-full border rounded-lg px-3 py-2"
            placeholder="잉크 이름을 입력하세요"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">카테고리</label>
          <select
            value={formData.inkCategory}
            onChange={e => setFormData(prev => ({ ...prev, inkCategory: e.target.value as FormData['inkCategory'] }))}
            className="w-full border rounded-lg px-3 py-2"
          >
            <option value="COLOR">COLOR</option>
            <option value="TRANSPARENT">TRANSPARENT</option>
            <option value="EFFECT">EFFECT</option>
            <option value="ADDITIVE">ADDITIVE</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">제조사</label>
          <input
            type="text"
            value={formData.manufacturer}
            onChange={e => setFormData(prev => ({ ...prev, manufacturer: e.target.value }))}
            className="w-full border rounded-lg px-3 py-2"
            placeholder="제조사 이름을 입력하세요"
          />
        </div>

        <div className="border rounded-lg p-4 bg-gray-50">
          <h3 className="font-semibold mb-3">SCI 색상 (L*a*b*)</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">L</label>
              <input
                type="number"
                step="0.1"
                min={0}
                max={100}
                value={formData.solidColorSci.L}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  solidColorSci: { ...prev.solidColorSci, L: parseFloat(e.target.value) || 0 }
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
                value={formData.solidColorSci.a}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  solidColorSci: { ...prev.solidColorSci, a: parseFloat(e.target.value) || 0 }
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
                value={formData.solidColorSci.b}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  solidColorSci: { ...prev.solidColorSci, b: parseFloat(e.target.value) || 0 }
                }))}
                className="w-full border rounded-lg px-3 py-2"
              />
            </div>
          </div>
        </div>

        <div className="border rounded-lg p-4 bg-gray-50">
          <h3 className="font-semibold mb-3">SCE 색상 (L*a*b*)</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">L</label>
              <input
                type="number"
                step="0.1"
                min={0}
                max={100}
                value={formData.solidColorSce.L}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  solidColorSce: { ...prev.solidColorSce, L: parseFloat(e.target.value) || 0 }
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
                value={formData.solidColorSce.a}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  solidColorSce: { ...prev.solidColorSce, a: parseFloat(e.target.value) || 0 }
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
                value={formData.solidColorSce.b}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  solidColorSce: { ...prev.solidColorSce, b: parseFloat(e.target.value) || 0 }
                }))}
                className="w-full border rounded-lg px-3 py-2"
              />
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">메모</label>
          <textarea
            value={formData.memo}
            onChange={e => setFormData(prev => ({ ...prev, memo: e.target.value }))}
            className="w-full border rounded-lg px-3 py-2"
            rows={3}
            placeholder="추가 메모를 입력하세요"
          />
        </div>

        <div className="flex gap-2">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? '생성 중...' : '잉크 생성'}
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
