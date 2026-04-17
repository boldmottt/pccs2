'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { inksApi, type InkResponse, type InkCreate } from '@/lib/api/inks'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Plus, Trash2, Edit2 } from 'lucide-react'

export default function InksPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingInk, setEditingInk] = useState<{ ink_id: string } | null>(null)
  const [formData, setFormData] = useState<InkCreate>({
    ink_name: '',
    ink_category: 'COLOR',
    manufacturer: '',
    solid_color_sci: { L: 0, a: 0, b: 0 },
    solid_color_sce: { L: 0, a: 0, b: 0 },
    gloss_GU: undefined,
    viscosity: undefined,
    density: undefined,
    memo: '',
  })

  const { data: inks, isLoading } = useQuery({
    queryKey: ['inks'],
    queryFn: () => inksApi.getAll(),
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingInk) {
        await inksApi.update(editingInk.ink_id, formData)
      } else {
        await inksApi.create(formData)
      }
      await queryClient.invalidateQueries({ queryKey: ['inks'] })
      resetForm()
    } catch (error) {
      console.error('Failed to save ink:', error)
      alert('잉크 저장에 실패했습니다.')
    }
  }

  const handleDelete = async (inkId: string) => {
    if (!confirm('정말 이 잉크를 삭제하시겠습니까?')) return
    try {
      await inksApi.delete(inkId)
      await queryClient.invalidateQueries({ queryKey: ['inks'] })
    } catch (error) {
      console.error('Failed to delete ink:', error)
      alert('잉크 삭제에 실패했습니다.')
    }
  }

  const handleEdit = (ink: InkResponse) => {
    setEditingInk({ ink_id: ink.ink_id })
    setFormData({
      ink_name: ink.ink_name,
      ink_category: ink.ink_category as any,
      manufacturer: ink.manufacturer || '',
      solid_color_sci: ink.solid_color_sci || { L: 0, a: 0, b: 0 },
      solid_color_sce: ink.solid_color_sce || { L: 0, a: 0, b: 0 },
      gloss_GU: ink.gloss_GU,
      viscosity: ink.viscosity,
      density: ink.density,
      memo: ink.memo || '',
    })
    setShowForm(true)
  }

  const resetForm = () => {
    setShowForm(false)
    setEditingInk(null)
    setFormData({
      ink_name: '',
      ink_category: 'COLOR',
      manufacturer: '',
      solid_color_sci: { L: 0, a: 0, b: 0 },
      solid_color_sce: { L: 0, a: 0, b: 0 },
      gloss_GU: undefined,
      viscosity: undefined,
      density: undefined,
      memo: '',
    })
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2">Inks</h1>
          <p className="text-text-secondary">잉크 마스터 데이터</p>
        </div>
        <Button onClick={() => { resetForm(); setShowForm(true); }}>
          <Plus className="w-4 h-4 mr-2" />
          잉크 추가
        </Button>
      </div>

      {showForm && (
        <div className="bg-bg-secondary/50 backdrop-blur-sm border border-border-subtle rounded-xl p-6 mb-6 animate-fade-in">
          <h2 className="text-xl font-semibold mb-4 text-text-primary">
            {editingInk ? '잉크 수정' : '잉크 추가'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1">
                  잉크 이름 *
                </label>
                <Input
                  value={formData.ink_name}
                  onChange={(e) => setFormData({ ...formData, ink_name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1">
                  카테고리
                </label>
                <select
                  value={formData.ink_category}
                  onChange={(e) => setFormData({ ...formData, ink_category: e.target.value as any })}
                  className="w-full h-10 px-3 py-2 bg-bg-secondary border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                >
                  <option value="COLOR">COLOR</option>
                  <option value="TRANSPARENT">TRANSPARENT</option>
                  <option value="EFFECT">EFFECT</option>
                  <option value="ADDITIVE">ADDITIVE</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">
                제조사
              </label>
              <Input
                value={formData.manufacturer || ''}
                onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-text-secondary mb-1">SCI - L</label>
                <Input
                  type="number"
                  value={formData.solid_color_sci?.L || 0}
                  onChange={(e) => setFormData({
                    ...formData,
                    solid_color_sci: { ...formData.solid_color_sci!, L: Number(e.target.value) }
                  })}
                />
              </div>
              <div>
                <label className="block text-xs text-text-secondary mb-1">SCI - a</label>
                <Input
                  type="number"
                  value={formData.solid_color_sci?.a || 0}
                  onChange={(e) => setFormData({
                    ...formData,
                    solid_color_sci: { ...formData.solid_color_sci!, a: Number(e.target.value) }
                  })}
                />
              </div>
              <div>
                <label className="block text-xs text-text-secondary mb-1">SCI - b</label>
                <Input
                  type="number"
                  value={formData.solid_color_sci?.b || 0}
                  onChange={(e) => setFormData({
                    ...formData,
                    solid_color_sci: { ...formData.solid_color_sci!, b: Number(e.target.value) }
                  })}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-text-secondary mb-1">SCE - L</label>
                <Input
                  type="number"
                  value={formData.solid_color_sce?.L || 0}
                  onChange={(e) => setFormData({
                    ...formData,
                    solid_color_sce: { ...formData.solid_color_sce!, L: Number(e.target.value) }
                  })}
                />
              </div>
              <div>
                <label className="block text-xs text-text-secondary mb-1">SCE - a</label>
                <Input
                  type="number"
                  value={formData.solid_color_sce?.a || 0}
                  onChange={(e) => setFormData({
                    ...formData,
                    solid_color_sce: { ...formData.solid_color_sce!, a: Number(e.target.value) }
                  })}
                />
              </div>
              <div>
                <label className="block text-xs text-text-secondary mb-1">SCE - b</label>
                <Input
                  type="number"
                  value={formData.solid_color_sce?.b || 0}
                  onChange={(e) => setFormData({
                    ...formData,
                    solid_color_sce: { ...formData.solid_color_sce!, b: Number(e.target.value) }
                  })}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">
                메모
              </label>
              <Input
                value={formData.memo || ''}
                onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
              />
            </div>

            <div className="flex gap-2 pt-2">
              <Button type="submit">저장</Button>
              <Button type="button" variant="ghost" onClick={resetForm}>
                취소
              </Button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-bg-secondary/50 backdrop-blur-sm border border-border-subtle rounded-xl overflow-hidden animate-fade-in">
        {isLoading ? (
          <div className="p-8 text-center text-text-secondary">로딩 중...</div>
        ) : inks && inks.length > 0 ? (
          <table className="w-full">
            <thead className="bg-bg-tertiary/50">
              <tr>
                <th className="text-left px-6 py-3 text-sm font-medium text-text-secondary">잉크 이름</th>
                <th className="text-left px-6 py-3 text-sm font-medium text-text-secondary">카테고리</th>
                <th className="text-left px-6 py-3 text-sm font-medium text-text-secondary">제조사</th>
                <th className="text-left px-6 py-3 text-sm font-medium text-text-secondary">메모</th>
                <th className="text-right px-6 py-3 text-sm font-medium text-text-secondary">작업</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {inks.map((ink) => (
                <tr key={ink.ink_id} className="hover:bg-bg-tertiary/30 transition-colors">
                  <td className="px-6 py-4 text-sm text-text-primary">{ink.ink_name}</td>
                  <td className="px-6 py-4 text-sm text-text-secondary">{ink.ink_category}</td>
                  <td className="px-6 py-4 text-sm text-text-secondary">{ink.manufacturer || '-'}</td>
                  <td className="px-6 py-4 text-sm text-text-secondary">{ink.memo || '-'}</td>
                  <td className="px-6 py-4 text-sm text-right">
                    <button
                       onClick={() => handleEdit(ink)}
                       className="text-accent-secondary hover:text-accent-primary mr-3 transition-colors"
                    >
                       <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                       onClick={() => handleDelete(ink.ink_id)}
                       className="text-error hover:text-red-400 transition-colors"
                    >
                       <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-16 text-center text-text-secondary">
            등록된 잉크가 없습니다.
          </div>
        )}
      </div>
    </div>
  )
}
