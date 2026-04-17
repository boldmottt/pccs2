'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Projects', href: '/projects' },
  { name: 'Samples', href: '/samples' },
  { name: 'Inks', href: '/inks' },
  { name: 'Match', href: '/match' },
]

export default function Header() {
  const pathname = usePathname()

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-bg-primary/80 backdrop-blur-xl border-b border-border-subtle">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center">
            <span className="text-xl font-bold text-gradient">PCCS2</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {navigation.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== '/match' && pathname?.startsWith(item.href))

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-[--duration-fast]',
                    isActive
                      ? 'bg-accent-primary/20 text-accent-primary'
                      : 'text-text-secondary hover:text-text-primary hover:bg-bg-secondary'
                  )}
                >
                  {item.name}
                </Link>
              )
            })}
          </div>
        </div>
      </nav>
    </header>
  )
}
