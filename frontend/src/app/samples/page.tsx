'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { samplesApi } from '@/lib/api/samples'
import { patternsApi } from '@/lib/api/patterns'
import { getErrorMessage } from '@/lib/api/client'
import type { Layer, Sample } from '@/lib/types/project'
import { Button } from '@/components/ui/Button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'
import { SuccessFlagBadge } from '@/components/samples/SuccessFlagBadge'
import { Plus, FileText, Copy } from 'lucide-react'

const COPIED_LAYER_KEY = 'pccs2-copied-layer'

function SampleRow({ sample }: { sample: Sample }) {
  const router = useRouter()

  const handleCopyLayer = (layer: Layer) => {
    sessionStorage.setItem(COPIED_LAYER_KEY, JSON.stringify(layer))
    router.push(`/samples/new?round_id=${sample.round_id}`)
  }

  return (
    <div className="p-4 flex flex-wrap items-center gap-4">
      <Link
        href={`/samples/${sample.sample_id}`}
        className="font-medium text-primary-700 hover:underline"
      >
        샘플 {sample.sample_number}
      </Link>
      <span className="text-sm text-gray-500">{sample.layers.length}개 레이어</span>
      <span className="text-sm text-gray-500">
        최종 ΔE:{' '}
        {sample.final_delta_e !== null && sample.final_delta_e !== undefined
          ? sample.final_delta_e.toFixed(2)
          : '-'}
      </span>
      <SuccessFlagBadge flag={sample.success_flag} />

      <div className="flex items-center gap-2 ml-auto">
        <span className="text-xs text-gray-400">배합비 복사:</span>
        {sample.layers.map(layer => (
          <Button
            key={layer.layer_number}
            variant="outline"
            size="sm"
            onClick={() => handleCopyLayer(layer)}
          >
            <Copy className="w-3 h-3 mr-1" />
            {layer.layer_number}도
          </Button>
        ))}
      </div>
    </div>
  )
}

export default function SamplesPage() {
  const router = useRouter()
  const [patternFilter, setPatternFilter] = useState<string>('')

  const patternsQuery = useQuery({
    queryKey: ['patterns'],
    queryFn: () => patternsApi.list(),
  })

  const samplesQuery = useQuery({
    queryKey: ['samples', { pattern_id: patternFilter || undefined }],
    queryFn: () => samplesApi.list(patternFilter ? { pattern_id: patternFilter } : undefined),
  })

  const selectedPattern = patternsQuery.data?.find(p => p.pattern_id === patternFilter)

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

      <div className="mb-4 max-w-sm">
        <label className="block text-sm font-medium text-gray-700 mb-1">패턴 필터</label>
        {patternsQuery.isLoading ? (
          <p className="text-sm text-gray-500">패턴을 불러오는 중...</p>
        ) : patternsQuery.isError ? (
          <div className="text-sm">
            <p className="text-red-600 mb-2">{getErrorMessage(patternsQuery.error)}</p>
            <Button variant="outline" size="sm" onClick={() => patternsQuery.refetch()}>
              다시 시도
            </Button>
          </div>
        ) : (
          <Select value={patternFilter} onValueChange={setPatternFilter}>
            <SelectTrigger>
              <SelectValue placeholder="전체 패턴">{selectedPattern?.pattern_name}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">전체 패턴</SelectItem>
              {(patternsQuery.data ?? []).map(pattern => (
                <SelectItem key={pattern.pattern_id} value={pattern.pattern_id}>
                  {pattern.pattern_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {samplesQuery.isLoading ? (
          <div className="p-8 text-center text-gray-500">샘플을 불러오는 중...</div>
        ) : samplesQuery.isError ? (
          <div className="p-8 text-center">
            <p className="text-red-600 mb-4">{getErrorMessage(samplesQuery.error)}</p>
            <Button variant="outline" onClick={() => samplesQuery.refetch()}>
              다시 시도
            </Button>
          </div>
        ) : samplesQuery.data && samplesQuery.data.length > 0 ? (
          <div className="divide-y divide-gray-100">
            {samplesQuery.data.map(sample => (
              <SampleRow key={sample.sample_id} sample={sample} />
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-600 mb-2">샘플이 없습니다.</h3>
            <p className="text-gray-400 mb-6">새로운 배합비 레시피를 등록하세요.</p>
            <Button onClick={() => router.push('/samples/new')}>
              <Plus className="w-4 h-4 mr-1" />
              샘플 등록하기
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
