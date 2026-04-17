'use client'

import React, { useContext, createContext } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

interface SelectContextType {
  value: string
  onValueChange: (value: string) => void
}

const SelectContext = createContext<SelectContextType | undefined>(undefined)

interface SelectOption {
  value: string
  label: string
}

interface SelectProps {
  value: string
  onValueChange: (value: string) => void
  options?: SelectOption[]
  placeholder?: string
  className?: string
  children?: React.ReactNode
}

export function Select({ value, onValueChange, options, placeholder, className, children }: SelectProps) {
  const selectedLabel = options?.find(o => o.value === value)?.label || placeholder || ''

  return (
    <SelectContext.Provider value={{ value, onValueChange }}>
      <div className={className}>
        {children || (
          <SelectTrigger>
            <SelectValue placeholder={placeholder}>{selectedLabel}</SelectValue>
          </SelectTrigger>
        )}
      </div>
    </SelectContext.Provider>
  )
}

interface SelectTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children?: React.ReactNode
}

export function SelectTrigger({ className, children, ...props }: SelectTriggerProps) {
  const context = useContext(SelectContext)
  const selectedLabel = context?.value
    ? React.Children.toArray(children).find(child =>
        React.isValidElement(child) &&
        (child as React.ReactElement).type === SelectValue
      )
    : null

  return (
    <button
      type="button"
      className={cn(
        'flex items-center justify-between w-full h-10 rounded-lg border border-border-subtle',
        'bg-bg-secondary/50 px-3 py-2 text-sm',
        'focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-accent-primary',
        'text-text-primary',
        className
      )}
      {...props}
    >
      <span className="truncate">{children || context?.value || ''}</span>
      <ChevronDown className="w-4 h-4 text-text-secondary" />
    </button>
  )
}

interface SelectContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export function SelectContent({ className, children, ...props }: SelectContentProps) {
  return (
    <div
      className={cn(
        'absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

interface SelectValueProps {
  placeholder?: string
  children?: React.ReactNode
}

export function SelectValue({ placeholder, children }: SelectValueProps) {
  const context = useContext(SelectContext)
  if (!context) return <span>{children || placeholder}</span>

  // If children provided, use it. Otherwise use placeholder or show selected value label
  if (children) {
    return <span>{children}</span>
  }

  // Find the label for selected value from options
  // This is passed down from parent Select component
  return <span>{placeholder || ''}</span>
}

interface SelectItemProps extends React.LiHTMLAttributes<HTMLLIElement> {
  value: string
  children: React.ReactNode
}

export function SelectItem({ value, children, className, onClick, ...props }: SelectItemProps) {
  const context = useContext(SelectContext)
  if (!context) throw new Error('SelectItem must be used within Select')

  const isSelected = context.value === value

  const handleClick = () => {
    context.onValueChange(value)
  }

  return (
    <li
      className={cn(
        'px-3 py-2 text-sm cursor-pointer hover:bg-gray-100',
        isSelected && 'bg-primary-50 text-primary-700',
        className
      )}
      onClick={handleClick}
      {...props}
    >
      {children}
    </li>
  )
}
