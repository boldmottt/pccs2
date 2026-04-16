'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/Button'
import { Plus, FileText } from 'lucide-react'

export default function SamplesPage() {
  const router = useRouter()

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">샘플 목록</h1>
          <p className="text-gray-600 mt-1">등록된 배합비 레시피 목록</p>
        </div>
        <Button onClick={() => router.push('/samples/new')}>
          <Plus className="w-4 h-4 mr-1" />
          새 샘플 등록
        </Button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-12 text-center">
          <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">샘플이 없습니다.</h3>
          <p className="text-gray-400 mb-6">새로운 배합비 레시피를 등록하세요.</p>
          <Button onClick={() => router.push('/samples/new')}>
            <Plus className="w-4 h-4 mr-1" />
            샘플 등록하기
          </Button>
        </div>
      </div>
    </div>
  )
}
