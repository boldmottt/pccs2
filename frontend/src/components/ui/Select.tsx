'use client'

import { useState, useContext, createContext } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

interface SelectContextType {
  value: string
  onValueChange: (value: string) => void
}

const SelectContext = createContext<SelectContextType | undefined>(undefined)

interface SelectProps {
  value: string
  onValueChange: (value: string) => void
  children: React.ReactNode
  className?: string
}

export function Select({ value, onValueChange, children, className }: SelectProps) {
  return (
    <SelectContext.Provider value={{ value, onValueChange }}>
      <div className={className}>{children}</div>
    </SelectContext.Provider>
  )
}

interface SelectTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children?: React.ReactNode
}

export function SelectTrigger({ className, children, ...props }: SelectTriggerProps) {
  return (
    <button
      type="button"
      className={cn(
        'flex items-center justify-between w-full h-10 rounded-lg border border-gray-300',
        'bg-white px-3 py-2 text-sm',
        'focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent',
        className
      )}
      {...props}
    >
      <span className="truncate">{children}</span>
      <ChevronDown className="w-4 h-4 text-gray-400" />
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
  return <span>{children || placeholder}</span>
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
