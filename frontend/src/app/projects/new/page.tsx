'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { projectsApi, type ProjectCreate } from '@/lib/api/projects'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export default function NewProjectPage() {
  const router = useRouter()
  const [formData, setFormData] = useState<ProjectCreate>({
    project_name: '',
    customer: '',
    start_date: undefined,
    target_completion: undefined,
    memo: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await projectsApi.create(formData)
      router.push('/projects')
    } catch (error) {
      console.error('Failed to create project:', error)
      alert('프로젝트 생성에 실패했습니다.')
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">프로젝트 추가</h1>
          <p className="text-gray-600 mt-1">새로운 프로젝트를 등록합니다</p>
        </div>
        <Button variant="outline" onClick={() => router.push('/projects')}>
          취소
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            프로젝트 이름 *
          </label>
          <Input
            value={formData.project_name}
            onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
            placeholder="프로젝트 이름을 입력하세요"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            고객사
          </label>
          <Input
            value={formData.customer || ''}
            onChange={(e) => setFormData({ ...formData, customer: e.target.value })}
            placeholder="고객사 이름을 입력하세요"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              시작일
            </label>
            <Input
              type="date"
              value={formData.start_date || ''}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              예상 완료일
            </label>
            <Input
              type="date"
              value={formData.target_completion || ''}
              onChange={(e) => setFormData({ ...formData, target_completion: e.target.value })}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            메모
          </label>
          <textarea
            value={formData.memo || ''}
            onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
            placeholder="프로젝트 메모를 입력하세요"
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div className="flex gap-2 justify-end">
          <Button type="button" variant="outline" onClick={() => router.push('/projects')}>
            취소
          </Button>
          <Button type="submit">
            프로젝트 생성
          </Button>
        </div>
      </form>
    </div>
  )
}
