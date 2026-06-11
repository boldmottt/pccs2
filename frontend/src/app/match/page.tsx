'use client'

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { patternsApi } from '@/lib/api/patterns'
import { inksApi } from '@/lib/api/inks'
import { matchApi, type MatchRequest, type RecommendedRecipe } from '@/lib/api/match'
import { getErrorMessage } from '@/lib/api/client'
import { labToCss, type Lab } from '@/lib/types/color'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'
import { ColorComparison } from '@/components/color/ColorComparison'
import { InkDonutChart, type InkData } from '@/components/visualization/InkDonutChart'
import { Wand2 } from 'lucide-react'

function RecipeCard({
  recipe,
  targetColor,
  inkName,
  inkColor,
}: {
  recipe: RecommendedRecipe
  targetColor: Lab
  inkName: (inkId: string) => string
  inkColor: (inkId: string) => string | undefined
}) {
  const inkData: InkData[] = recipe.recipe.map(item => ({
    inkId: item.ink_id,
    inkName: inkName(item.ink_id),
    amount: item.amount,
    color: inkColor(item.ink_id),
  }))
  const totalAmount = inkData.reduce((sum, ink) => sum + ink.amount, 0)

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>추천 {recipe.rank}위</CardTitle>
          <span className="text-sm text-gray-500">
            신뢰도: {(recipe.confidence_score * 100).toFixed(0)}%
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-start gap-6">
          <InkDonutChart inks={inkData} totalAmount={totalAmount} size="sm" showLabels={false} />
          <div className="flex-1 min-w-[180px] space-y-1">
            {inkData.map(item => (
              <div key={item.inkId} className="flex items-center justify-between text-sm">
                <span className="font-medium">{item.inkName}</span>
                <span className="text-gray-500">
                  {item.amount.toFixed(1)}g
                  {totalAmount > 0 ? ` (${((item.amount / totalAmount) * 100).toFixed(0)}%)` : ''}
                </span>
              </div>
            ))}
            <div className="pt-2 text-sm text-gray-600">
              권장 신너 비율: {(recipe.suggested_thinner_ratio * 100).toFixed(0)}%
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-gray-100">
          <ColorComparison
            color1={targetColor}
            color2={recipe.predicted_color}
            label1="목표 색상"
            label2="예측 색상"
            deltaE={recipe.predicted_delta_E}
          />
        </div>
      </CardContent>
    </Card>
  )
}

export default function MatchPage() {
  const [patternId, setPatternId] = useState('')
  const [targetColor, setTargetColor] = useState<Lab>({ L: 50, a: 0, b: 0 })
  const [layerNumber, setLayerNumber] = useState('1')
  const [maxComponents, setMaxComponents] = useState('3')
  const [formError, setFormError] = useState<string | null>(null)

  const patternsQuery = useQuery({
    queryKey: ['patterns'],
    queryFn: () => patternsApi.list(),
  })

  const inksQuery = useQuery({
    queryKey: ['inks'],
    queryFn: () => inksApi.list(),
  })

  const matchMutation = useMutation({
    mutationFn: (data: MatchRequest) => matchApi.match(data),
  })

  const selectedPattern = patternsQuery.data?.find(p => p.pattern_id === patternId)

  const inkName = (inkId: string) =>
    inksQuery.data?.find(i => i.ink_id === inkId)?.ink_name || inkId

  // 측색값이 있으면 실제 잉크 색 (없으면 차트 내장 팔레트 사용)
  const inkColor = (inkId: string) => {
    const sci = inksQuery.data?.find(i => i.ink_id === inkId)?.solid_color_sci
    return sci ? labToCss(sci) : undefined
  }

  const handlePatternChange = (id: string) => {
    setPatternId(id)
    const pattern = patternsQuery.data?.find(p => p.pattern_id === id)
    if (pattern?.target_base_color_sci) {
      setTargetColor(pattern.target_base_color_sci)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    if (!patternId) {
      setFormError('패턴을 선택하세요.')
      return
    }
    matchMutation.mutate({
      pattern_id: patternId,
      target_color: targetColor,
      layer_number: Math.max(1, Number(layerNumber) || 1),
      max_components: Math.min(3, Math.max(1, Number(maxComponents) || 3)),
    })
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Wand2 className="w-7 h-7 text-primary-600" />
          배합 추천
        </h1>
        <p className="text-gray-600 mt-1">AI 기반 잉크 배합비 추천</p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        {patternsQuery.isLoading ? (
          <p className="text-gray-500">패턴을 불러오는 중...</p>
        ) : patternsQuery.isError ? (
          <div>
            <p className="text-red-600 mb-3">{getErrorMessage(patternsQuery.error)}</p>
            <Button variant="outline" onClick={() => patternsQuery.refetch()}>
              다시 시도
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="max-w-sm">
              <label className="block text-sm font-medium text-gray-700 mb-1">패턴 *</label>
              <Select value={patternId} onValueChange={handlePatternChange}>
                <SelectTrigger>
                  <SelectValue placeholder="패턴 선택">{selectedPattern?.pattern_name}</SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {(patternsQuery.data ?? []).map(pattern => (
                    <SelectItem key={pattern.pattern_id} value={pattern.pattern_id}>
                      {pattern.pattern_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">목표 색상 (L*, a*, b*)</p>
              <div className="grid grid-cols-3 gap-3 max-w-md">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">L*</label>
                  <input
                    type="number"
                    value={targetColor.L}
                    onChange={e => setTargetColor({ ...targetColor, L: Number(e.target.value) })}
                    className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
                    min="0"
                    max="100"
                    step="0.01"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">a*</label>
                  <input
                    type="number"
                    value={targetColor.a}
                    onChange={e => setTargetColor({ ...targetColor, a: Number(e.target.value) })}
                    className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
                    min="-128"
                    max="127"
                    step="0.01"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">b*</label>
                  <input
                    type="number"
                    value={targetColor.b}
                    onChange={e => setTargetColor({ ...targetColor, b: Number(e.target.value) })}
                    className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
                    min="-128"
                    max="127"
                    step="0.01"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 max-w-md">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">레이어 번호</label>
                <input
                  type="number"
                  value={layerNumber}
                  onChange={e => setLayerNumber(e.target.value)}
                  className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">최대 잉크 수</label>
                <Select value={maxComponents} onValueChange={setMaxComponents}>
                  <SelectTrigger>
                    <SelectValue>{maxComponents}개</SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {['1', '2', '3'].map(n => (
                      <SelectItem key={n} value={n}>
                        {n}개
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {formError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {formError}
              </div>
            )}

            <Button type="submit" disabled={matchMutation.isPending}>
              {matchMutation.isPending ? '추천 중...' : '배합 추천 받기'}
            </Button>
          </form>
        )}
      </div>

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

      {matchMutation.isError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          배합 추천에 실패했습니다: {getErrorMessage(matchMutation.error)}
        </div>
      )}

      {matchMutation.data && (
        <div>
          <h2 className="text-xl font-semibold mb-4">추천 배합비</h2>
          {matchMutation.data.recommended_recipes.length === 0 ? (
            <div className="p-8 text-center text-gray-500 bg-white rounded-lg border border-gray-200">
              추천 가능한 배합비가 없습니다.
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {matchMutation.data.recommended_recipes.map(recipe => (
                <RecipeCard
                  key={recipe.rank}
                  recipe={recipe}
                  targetColor={targetColor}
                  inkName={inkName}
                  inkColor={inkColor}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
