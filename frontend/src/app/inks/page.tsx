'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { inksApi } from '@/lib/api/inks'
import { Button } from '@/components/ui/Button'

export default function InksPage() {
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>(undefined)

  const { data: inks = [], isLoading } = useQuery({
    queryKey: ['inks', selectedCategory],
    queryFn: () => inksApi.getAll(selectedCategory),
  })

  const categories = ['COLOR', 'TRANSPARENT', 'EFFECT', 'ADDITIVE']

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">잉크 목록</h1>
        <Link href="/inks/new">
          <Button>새 잉크 추가</Button>
        </Link>
      </div>

      <div className="mb-4">
        <Button
          variant={selectedCategory === undefined ? 'primary' : 'outline'}
          onClick={() => setSelectedCategory(undefined)}
        >
          전체
        </Button>
        {categories.map(cat => (
          <Button
            key={cat}
            variant={selectedCategory === cat ? 'primary' : 'outline'}
            className="ml-2"
            onClick={() => setSelectedCategory(cat)}
          >
            {cat}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <div className="text-center py-8">로딩 중...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {inks.map((ink: any) => (
            <Link key={ink.inkId} href={`/inks/${ink.inkId}`}>
              <div className="border rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer bg-white">
                <h3 className="font-semibold text-lg">{ink.inkName}</h3>
                <p className="text-sm text-gray-600">카테고리: {ink.inkCategory}</p>
                <p className="text-sm text-gray-600">제조사: {ink.manufacturer || '없음'}</p>
              </div>
            </Link>
          ))}
          {inks.length === 0 && (
            <div className="text-center py-8 text-gray-500">잉크가 없습니다.</div>
          )}
        </div>
      )}
    </div>
  )
}
