'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/Button'
import { Plus, FileText } from 'lucide-react'

export default function SamplesPage() {
  const router = useRouter()

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2">Samples</h1>
          <p className="text-text-secondary">등록된 배합비 레시피 목록</p>
        </div>
        <Button onClick={() => router.push('/samples/new')}>
          <Plus className="w-4 h-4 mr-1" />
          새 샘플 등록
        </Button>
      </div>

      {/* Content Card */}
      <div className="bg-bg-secondary/50 backdrop-blur-sm border border-border-subtle rounded-xl overflow-hidden">
        <div className="p-16 text-center">
          <FileText className="w-16 h-16 text-text-secondary mx-auto mb-4" />
          <h3 className="text-lg font-medium text-text-primary mb-2">샘플이 없습니다.</h3>
          <p className="text-text-secondary mb-6">새로운 배합비 레시피를 등록하세요.</p>
          <Button onClick={() => router.push('/samples/new')}>
            <Plus className="w-4 h-4 mr-1" />
            샘플 등록하기
          </Button>
        </div>
      </div>
    </div>
  )
}
