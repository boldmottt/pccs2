import { ColorSwatch } from './ColorSwatch'
import type { Lab } from '@/lib/types/color'

interface ColorComparisonProps {
  color1: Lab
  color2: Lab
  label1?: string
  label2?: string
  deltaE?: number
}

export function ColorComparison({
  color1,
  color2,
  label1 = '목표',
  label2 = '샘플',
  deltaE
}: ColorComparisonProps) {
  return (
    <div className="flex items-center gap-4">
      <ColorSwatch color={color1} label={label1} size="lg" />
      <div className="flex flex-col items-center px-4">
        {deltaE !== undefined && (
          <>
            <span className="text-sm font-medium text-gray-700">ΔE = {deltaE.toFixed(2)}</span>
            <span
              className={`text-xs mt-1 ${
                deltaE < 2 ? 'text-green-600' : deltaE < 5 ? 'text-orange-600' : 'text-red-600'
              }`}
            >
              {deltaE < 2 ? '허용 범위' : deltaE < 5 ? '허용 오차 초과' : '큰 차이'}
            </span>
          </>
        )}
      </div>
      <ColorSwatch color={color2} label={label2} size="lg" />
    </div>
  )
}
