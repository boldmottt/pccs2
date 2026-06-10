'use client'

import { use } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { samplesApi } from '@/lib/api/samples'
import { patternsApi } from '@/lib/api/patterns'
import { inksApi } from '@/lib/api/inks'
import { getErrorMessage } from '@/lib/api/client'
import type { Layer } from '@/lib/types/project'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { ColorSwatch } from '@/components/color/ColorSwatch'
import { ColorComparison } from '@/components/color/ColorComparison'
import { SuccessFlagBadge } from '@/components/samples/SuccessFlagBadge'
import { ArrowLeft } from 'lucide-react'

function LayerCard({ layer, inkName }: { layer: Layer; inkName: (inkId: string) => string }) {
  const totalAmount = layer.ink_items.reduce((sum, item) => sum + item.amount, 0)

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>{layer.layer_number}도</CardTitle>
          <span className="text-sm text-gray-500">총량: {totalAmount.toFixed(1)}g</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          {layer.ink_items.map((item, index) => (
            <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-sm">
              <span className="font-medium">{inkName(item.ink_id)}</span>
              <span className="text-gray-500">
                {item.amount.toFixed(1)}g
                {totalAmount > 0 ? ` (${((item.amount / totalAmount) * 100).toFixed(0)}%)` : ''}
              </span>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          {layer.thinner_pct !== null && layer.thinner_pct !== undefined && (
            <span>신너: {layer.thinner_pct}%</span>
          )}
          {layer.hardener_pct !== null && layer.hardener_pct !== undefined && (
            <span>경화제: {layer.hardener_pct}%</span>
          )}
          {layer.delta_E_from_target !== null && layer.delta_E_from_target !== undefined && (
            <span>목표 대비 ΔE: {layer.delta_E_from_target.toFixed(2)}</span>
          )}
        </div>

        {(layer.print_color_sci || layer.print_color_sce) && (
          <div className="flex items-center gap-6 pt-2 border-t border-gray-100">
            {layer.print_color_sci && (
              <ColorSwatch color={layer.print_color_sci} label="인쇄 색상 SCI" size="md" />
            )}
            {layer.print_color_sce && (
              <ColorSwatch color={layer.print_color_sce} label="인쇄 색상 SCE" size="md" />
            )}
          </div>
        )}

        {layer.note && <p className="text-sm text-gray-500">{layer.note}</p>}
      </CardContent>
    </Card>
  )
}

export default function SampleDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)

  const sampleQuery = useQuery({
    queryKey: ['samples', 'detail', id],
    queryFn: () => samplesApi.get(id),
  })

  const sample = sampleQuery.data

  const patternQuery = useQuery({
    queryKey: ['patterns', 'detail', sample?.pattern_id],
    queryFn: () => patternsApi.get(sample!.pattern_id),
    enabled: !!sample,
  })

  const inksQuery = useQuery({
    queryKey: ['inks'],
    queryFn: () => inksApi.list(),
  })

  const inkName = (inkId: string) =>
    inksQuery.data?.find(i => i.ink_id === inkId)?.ink_name || inkId

  if (sampleQuery.isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="p-8 text-center text-gray-500 bg-white rounded-lg border border-gray-200">
          샘플을 불러오는 중...
        </div>
      </div>
    )
  }

  if (sampleQuery.isError || !sample) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="p-8 text-center bg-white rounded-lg border border-gray-200">
          <p className="text-red-600 mb-4">{getErrorMessage(sampleQuery.error)}</p>
          <Button variant="outline" onClick={() => sampleQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      </div>
    )
  }

  const finalPrintColor = [...sample.layers]
    .reverse()
    .find(l => l.print_color_sci)?.print_color_sci

  const targetColor = patternQuery.data?.target_base_color_sci

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <Link
        href={`/patterns/${sample.pattern_id}`}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 mb-6 transition-colors w-fit"
      >
        <ArrowLeft className="w-4 h-4" />
        패턴 상세
      </Link>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold">샘플 {sample.sample_number}</h1>
            <p className="text-gray-600 mt-1">베이스 소재: {sample.base_material}</p>
          </div>
          <div className="flex items-center gap-3">
            {sample.final_delta_e !== null && sample.final_delta_e !== undefined && (
              <span className="text-sm text-gray-600">
                최종 ΔE: <strong>{sample.final_delta_e.toFixed(2)}</strong>
              </span>
            )}
            <SuccessFlagBadge flag={sample.success_flag} />
          </div>
        </div>

        <div className="flex items-center gap-6">
          <ColorSwatch color={sample.base_color_sci} label="베이스 SCI" size="lg" />
          <ColorSwatch color={sample.base_color_sce} label="베이스 SCE" size="lg" />
        </div>

        {sample.success_notes && (
          <p className="text-sm text-gray-500 mt-4">{sample.success_notes}</p>
        )}
      </div>

      {targetColor && finalPrintColor && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">목표 색상 비교</h2>
          <ColorComparison
            color1={targetColor}
            color2={finalPrintColor}
            label1="목표 색상"
            label2="최종 인쇄 색상"
            deltaE={sample.final_delta_e ?? undefined}
          />
        </div>
      )}

      {patternQuery.isLoading && (
        <div className="p-4 mb-6 text-center text-sm text-gray-500 bg-white rounded-lg border border-gray-200">
          패턴 정보를 불러오는 중...
        </div>
      )}
      {patternQuery.isError && (
        <div className="p-4 mb-6 text-center bg-white rounded-lg border border-gray-200">
          <p className="text-sm text-red-600 mb-2">{getErrorMessage(patternQuery.error)}</p>
          <Button variant="outline" size="sm" onClick={() => patternQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      )}

      <h2 className="text-xl font-semibold mb-4">레이어</h2>
      {inksQuery.isLoading && (
        <p className="text-sm text-gray-500 mb-3">잉크 이름을 불러오는 중...</p>
      )}
      {inksQuery.isError && (
        <div className="mb-3 text-sm">
          <span className="text-red-600 mr-2">{getErrorMessage(inksQuery.error)}</span>
          <Button variant="outline" size="sm" onClick={() => inksQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      )}
      <div className="space-y-4">
        {sample.layers.map(layer => (
          <LayerCard key={layer.layer_number} layer={layer} inkName={inkName} />
        ))}
      </div>
    </div>
  )
}
