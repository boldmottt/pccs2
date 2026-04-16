'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '@/lib/api/projects'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { ArrowLeft } from 'lucide-react'

interface ProjectFormData {
  project_name: string
  customer: string
  start_date: string
  target_completion: string
  memo: string
}

export default function NewProjectPage() {
  const router = useRouter()
  const queryClient = useQueryClient()

  const [form, setForm] = useState<ProjectFormData>({
    project_name: '',
    customer: '',
    start_date: new Date().toISOString().split('T')[0],
    target_completion: '',
    memo: '',
  })

  const [errors, setErrors] = useState<Partial<Record<keyof ProjectFormData, string>>>({})

  const mutation = useMutation({
    mutationFn: (data: ProjectFormData) => {
      const payload: Record<string, unknown> = {
        project_name: data.project_name,
      }
      if (data.customer) payload.customer = data.customer
      if (data.start_date) payload.start_date = data.start_date
      if (data.target_completion) payload.target_completion = data.target_completion
      if (data.memo) payload.memo = data.memo
      return projectsApi.create(payload as Parameters<typeof projectsApi.create>[0])
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      router.push('/projects')
    },
  })

  const validate = (): boolean => {
    const newErrors: typeof errors = {}
    if (!form.project_name.trim()) {
      newErrors.project_name = '프로젝트 이름을 입력하세요'
    }
    if (form.target_completion && form.start_date && form.target_completion < form.start_date) {
      newErrors.target_completion = '목표 완료일은 시작일 이후여야 합니다'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    mutation.mutate(form)
  }

  const updateField = (field: keyof ProjectFormData, value: string) => {
    setForm({ ...form, [field]: value })
    if (errors[field]) {
      setErrors({ ...errors, [field]: undefined })
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <button
        onClick={() => router.push('/projects')}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        프로젝트 목록
      </button>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">새 프로젝트</h1>
        <p className="text-gray-600 mt-1">프로젝트 정보를 입력하세요</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-5">
          <Input
            id="project_name"
            label="프로젝트 이름 *"
            placeholder="예: 고객사A 빨간색 잉크"
            value={form.project_name}
            onChange={e => updateField('project_name', e.target.value)}
            error={errors.project_name}
            autoFocus
          />

          <Input
            id="customer"
            label="고객사"
            placeholder="고객사 이름"
            value={form.customer}
            onChange={e => updateField('customer', e.target.value)}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              id="start_date"
              label="시작일"
              type="date"
              value={form.start_date}
              onChange={e => updateField('start_date', e.target.value)}
            />
            <Input
              id="target_completion"
              label="목표 완료일"
              type="date"
              value={form.target_completion}
              onChange={e => updateField('target_completion', e.target.value)}
              error={errors.target_completion}
            />
          </div>

          <div>
            <label htmlFor="memo" className="block text-sm font-medium text-gray-700 mb-1">
              메모
            </label>
            <textarea
              id="memo"
              rows={3}
              placeholder="프로젝트 관련 메모"
              value={form.memo}
              onChange={e => updateField('memo', e.target.value)}
              className="flex w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent resize-none"
            />
          </div>
        </div>

        {mutation.isError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            프로젝트 생성에 실패했습니다. 다시 시도해주세요.
          </div>
        )}

        <div className="flex justify-end gap-3 mt-6">
          <Button variant="outline" type="button" onClick={() => router.push('/projects')}>
            취소
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? '생성 중...' : '프로젝트 생성'}
          </Button>
        </div>
      </form>
    </div>
  )
}
