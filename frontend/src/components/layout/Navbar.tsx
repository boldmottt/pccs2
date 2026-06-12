'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Palette, FolderKanban, Beaker, FlaskConical, Wand2, Database, Square, GitBranch } from 'lucide-react'
import { clsx } from 'clsx'

const NAV_ITEMS = [
  { href: '/projects', label: '프로젝트', Icon: FolderKanban },
  { href: '/samples', label: '샘플', Icon: FlaskConical },
  { href: '/inks', label: '잉크', Icon: Beaker },
  { href: '/bases', label: '베이스', Icon: Square },
  { href: '/blends', label: '배합 계층', Icon: GitBranch },
  { href: '/match', label: '배합 추천', Icon: Wand2 },
  { href: '/import', label: 'RDP 가져오기', Icon: Database },
]

export function Navbar() {
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white/90 backdrop-blur">
      <nav className="max-w-7xl mx-auto px-4 flex items-center gap-1 h-14 overflow-x-auto">
        <Link
          href="/"
          className="flex items-center gap-2 font-bold text-lg text-primary-700 mr-4 shrink-0"
        >
          <Palette className="w-5 h-5" />
          PCCS2
        </Link>

        {NAV_ITEMS.map(({ href, label, Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`)
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium whitespace-nowrap transition-colors',
                active
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          )
        })}
      </nav>
    </header>
  )
}
