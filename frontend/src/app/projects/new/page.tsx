'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { projectsApi } from '@/lib/api/projects'
import { Button } from '@/components/ui/Button'

type FormData = {
  projectName: string
  customer: string
  memo: string
}

export default function NewProjectPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<FormData>({
    projectName: '',
    customer: '',
    memo: '',
  })

  const mutation = useMutation({
    mutationFn: projectsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      router.push('/projects')
    },
    onError: (error: Error) => {
      console.error('Failed to create project:', error)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate({
      projectName: formData.projectName,
      customer: formData.customer || undefined,
      memo: formData.memo || undefined,
    })
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">새 프로젝트</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">프로젝트명 *</label>
          <input
            type="text"
            required
            value={formData.projectName}
            onChange={e => setFormData(prev => ({ ...prev, projectName: e.target.value }))}
            className="w-full border rounded-lg px-3 py-2"
            placeholder="프로젝트 이름을 입력하세요"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">고객사</label>
          <input
            type="text"
            value={formData.customer}
            onChange={e => setFormData(prev => ({ ...prev, customer: e.target.value }))}
            className="w-full border rounded-lg px-3 py-2"
            placeholder="고객사 이름을 입력하세요"
          />
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
            {mutation.isPending ? '생성 중...' : '프로젝트 생성'}
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
