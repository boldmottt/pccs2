'use client'

import { useState } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import type { Ink } from '@/lib/types/project'

interface InkSelectorProps {
  inks: Ink[]
  onSelect: (ink: Ink, amount: number) => void
  defaultAmount?: number
}

export function InkSelector({ inks, onSelect, defaultAmount = 10 }: InkSelectorProps) {
  const [selectedInk, setSelectedInk] = useState<string>('')
  const [amount, setAmount] = useState<number>(defaultAmount)

  // 정렬: ⭐ 기본잉크처럼 사용 → 원료 잉크 → 일반 배합 잉크, 각 그룹 내 이름순
  const sorted = [...inks].sort((a, b) => {
    const rank = (i: Ink) => (i.is_favorite ? 0 : !i.is_blend_ink ? 1 : 2)
    return rank(a) - rank(b) || a.ink_name.localeCompare(b.ink_name)
  })

  const selected = inks.find(i => i.ink_id === selectedInk)

  const handleAdd = () => {
    if (selected && amount > 0) {
      onSelect(selected, amount)
      setAmount(defaultAmount)
    }
  }

  return (
    <div className="flex flex-wrap gap-3 items-end">
      <div className="flex-1 min-w-[200px]">
        <Select value={selectedInk} onValueChange={setSelectedInk}>
          <SelectTrigger>
            <SelectValue placeholder="잉크 선택">{selected?.ink_name}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {sorted.length === 0 ? (
              <li className="px-3 py-2 text-sm text-gray-400">등록된 잉크가 없습니다.</li>
            ) : (
              sorted.map(ink => (
                <SelectItem key={ink.ink_id} value={ink.ink_id}>
                  {ink.is_favorite ? '⭐ ' : ''}
                  {ink.ink_name}
                  <span className="ml-2 text-xs text-gray-400">
                    {ink.ink_category}
                    {ink.is_blend_ink ? ' · 배합' : ''}
                  </span>
                </SelectItem>
              ))
            )}
          </SelectContent>
        </Select>
      </div>

      <div className="w-24">
        <label className="block text-xs text-gray-500 mb-1">량 (g)</label>
        <input
          type="number"
          value={amount}
          onChange={e => setAmount(Math.max(0, Number(e.target.value)))}
          className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
          min="0"
          step="0.1"
        />
      </div>

      <Button onClick={handleAdd} disabled={!selectedInk || amount <= 0}>
        추가
      </Button>
    </div>
  )
}
