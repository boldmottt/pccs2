'use client'

import { useState, useContext, createContext, useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

interface SelectContextType {
  value: string
  onValueChange: (value: string) => void
  open: boolean
  setOpen: (open: boolean) => void
}

const SelectContext = createContext<SelectContextType | undefined>(undefined)

function useSelectContext(component: string): SelectContextType {
  const context = useContext(SelectContext)
  if (!context) throw new Error(`${component} must be used within Select`)
  return context
}

interface SelectProps {
  value: string
  onValueChange: (value: string) => void
  children: React.ReactNode
  className?: string
}

export function Select({ value, onValueChange, children, className }: SelectProps) {
  const [open, setOpen] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return

    const handleMouseDown = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handleMouseDown)
    return () => document.removeEventListener('mousedown', handleMouseDown)
  }, [open])

  return (
    <SelectContext.Provider value={{ value, onValueChange, open, setOpen }}>
      <div ref={wrapperRef} className={cn('relative', className)}>
        {children}
      </div>
    </SelectContext.Provider>
  )
}

interface SelectTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children?: React.ReactNode
}

export function SelectTrigger({ className, children, onClick, ...props }: SelectTriggerProps) {
  const { open, setOpen } = useSelectContext('SelectTrigger')

  return (
    <button
      type="button"
      aria-haspopup="listbox"
      aria-expanded={open}
      onClick={event => {
        setOpen(!open)
        onClick?.(event)
      }}
      className={cn(
        'flex items-center justify-between w-full h-10 rounded-lg border border-gray-300',
        'bg-white px-3 py-2 text-sm',
        'focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent',
        className
      )}
      {...props}
    >
      <span className="truncate">{children}</span>
      <ChevronDown
        className={cn('w-4 h-4 text-gray-400 shrink-0 transition-transform', open && 'rotate-180')}
      />
    </button>
  )
}

interface SelectContentProps extends React.HTMLAttributes<HTMLUListElement> {
  children: React.ReactNode
}

export function SelectContent({ className, children, ...props }: SelectContentProps) {
  const { open } = useSelectContext('SelectContent')

  if (!open) return null

  return (
    <ul
      role="listbox"
      className={cn(
        'absolute left-0 right-0 z-50 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto py-1',
        className
      )}
      {...props}
    >
      {children}
    </ul>
  )
}

interface SelectValueProps {
  placeholder?: string
  children?: React.ReactNode
}

export function SelectValue({ placeholder, children }: SelectValueProps) {
  if (children) return <span>{children}</span>
  return <span className="text-gray-400">{placeholder}</span>
}

interface SelectItemProps extends React.LiHTMLAttributes<HTMLLIElement> {
  value: string
  children: React.ReactNode
}

export function SelectItem({ value, children, className, onClick, ...props }: SelectItemProps) {
  const { value: selectedValue, onValueChange, setOpen } = useSelectContext('SelectItem')

  const isSelected = selectedValue === value

  return (
    <li
      role="option"
      aria-selected={isSelected}
      className={cn(
        'px-3 py-2 text-sm cursor-pointer hover:bg-gray-100',
        isSelected && 'bg-primary-50 text-primary-700',
        className
      )}
      onClick={event => {
        onValueChange(value)
        setOpen(false)
        onClick?.(event)
      }}
      {...props}
    >
      {children}
    </li>
  )
}
