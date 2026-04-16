import { cn } from '@/lib/utils'

interface CardProps {
  className?: string
  children: React.ReactNode
}

export function Card({ className, children }: CardProps) {
  return (
    <div className={cn('rounded-lg border border-gray-200 bg-white shadow-sm', className)}>
      {children}
    </div>
  )
}

interface CardHeaderProps {
  className?: string
  children: React.ReactNode
}

export function CardHeader({ className, children }: CardHeaderProps) {
  return <div className={cn('p-4 border-b border-gray-200', className)}>{children}</div>
}

interface CardTitleProps {
  className?: string
  children: React.ReactNode
}

export function CardTitle({ className, children }: CardTitleProps) {
  return <h3 className={cn('text-lg font-semibold', className)}>{children}</h3>
}

interface CardContentProps {
  className?: string
  children: React.ReactNode
}

export function CardContent({ className, children }: CardContentProps) {
  return <div className={cn('p-4', className)}>{children}</div>
}
