'use client'

import { LayerEditor } from './LayerEditor'
import { InkSelector } from './InkSelector'
import type { Ink, InkItem } from '@/lib/types/project'

interface LayerEditorWithSelectorProps {
  layerNumber: number
  inkItems: InkItem[]
  thinnerPct?: number
  hardenerPct?: number
  inks: Ink[]
  onInksChange: (items: InkItem[]) => void
  onAddInk: (ink: Ink, amount: number) => void
  onThinnerChange: (value: number) => void
  onHardenerChange: (value: number) => void
}

export function LayerEditorWithSelector({
  layerNumber,
  inkItems,
  thinnerPct,
  hardenerPct,
  inks,
  onInksChange,
  onAddInk,
  onThinnerChange,
  onHardenerChange,
}: LayerEditorWithSelectorProps) {
  return (
    <div className="space-y-4">
      <InkSelector inks={inks} onSelect={onAddInk} />
      <LayerEditor
        layerNumber={layerNumber}
        inkItems={inkItems}
        thinnerPct={thinnerPct}
        hardenerPct={hardenerPct}
        inks={inks}
        onInksChange={onInksChange}
        onThinnerChange={onThinnerChange}
        onHardenerChange={onHardenerChange}
      />
    </div>
  )
}
