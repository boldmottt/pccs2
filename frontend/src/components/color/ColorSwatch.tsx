import { convertLabToRgb } from '@/lib/types/color'

interface ColorSwatchProps {
  color: { L: number; a: number; b: number }
  label?: string
  size?: 'sm' | 'md' | 'lg'
}

export function ColorSwatch({ color, label, size = 'md' }: ColorSwatchProps) {
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
