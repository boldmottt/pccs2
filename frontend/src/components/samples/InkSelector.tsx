'use client'

import { useState } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'

export interface Ink {
  inkId: string
  inkName: string
  category: string
}

interface InkSelectorProps {
  inks: Ink[]
  onSelect: (ink: Ink, amount: number) => void
  defaultAmount?: number
}

export function InkSelector({ inks, onSelect, defaultAmount = 10 }: InkSelectorProps) {
  const [selectedInk, setSelectedInk] = useState<string>('')
  const [amount, setAmount] = useState<number>(defaultAmount)

  const handleAdd = () => {
    const ink = inks.find(i => i.inkId === selectedInk)
    if (ink && amount > 0) {
      onSelect(ink, amount)
      setAmount(10) // Reset to default
    }
  }

  return (
    <div className="flex flex-wrap gap-3 items-end">
      <div className="flex-1 min-w-[200px]">
        <Select value={selectedInk} onValueChange={setSelectedInk}>
          <SelectTrigger>
            <SelectValue placeholder="잉크 선택" />
          </SelectTrigger>
          <SelectContent>
            {inks.map(ink => (
              <SelectItem key={ink.inkId} value={ink.inkId}>
                {ink.inkName}
              </SelectItem>
            ))}
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
