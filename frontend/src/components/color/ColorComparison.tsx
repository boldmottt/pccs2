import { cn } from '@/lib/utils'
import { convertLabToRgb } from '@/lib/types/color'
import type { ColorXYZ } from '@/lib/types/color'

interface ColorSwatchProps {
  color: ColorXYZ
  label?: string
  size?: 'sm' | 'md' | 'lg'
}

function ColorSwatch({ color, label, size = 'md' }: ColorSwatchProps) {
  const rgb = convertLabToRgb(color.L, color.a, color.b)
  const backgroundColor = `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`

  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16'
  }

  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className={cn(
          'rounded-lg shadow-md border border-gray-200',
          sizeClasses[size]
        )}
        style={{ backgroundColor }}
      />
      {label && <span className="text-xs text-gray-600">{label}</span>}
    </div>
  )
}

interface ColorComparisonProps {
  color1: ColorXYZ
  color2: ColorXYZ
  label1?: string
  label2?: string
  deltaE?: number
}

export function ColorComparison({
  color1,
  color2,
  label1 = 'Target',
  label2 = 'Sample',
  deltaE
}: ColorComparisonProps) {
  return (
    <div className="flex items-center gap-4">
      <ColorSwatch color={color1} label={label1} size="lg" />
      <div className="flex flex-col items-center px-4">
        <span className="text-sm font-medium text-gray-700">ΔE = {deltaE?.toFixed(2)}</span>
        {deltaE !== undefined && (
          <span className={`text-xs mt-1 ${
            deltaE < 2 ? 'text-green-600' :
            deltaE < 5 ? 'text-orange-600' :
            'text-red-600'
          }`}>
            {deltaE < 2 ? 'Acceptable' : deltaE < 5 ? 'Outside tolerance' : 'Significant difference'}
          </span>
        )}
      </div>
      <ColorSwatch color={color2} label={label2} size="lg" />
    </div>
  )
}
