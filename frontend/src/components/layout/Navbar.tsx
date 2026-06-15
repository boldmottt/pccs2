'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Palette,
  FolderKanban,
  Beaker,
  FlaskConical,
  Wand2,
  Database,
  Square,
  GitBranch,
  Table2,
  Menu,
  X,
} from 'lucide-react'
import { clsx } from 'clsx'

const NAV_ITEMS = [
  { href: '/projects', label: '프로젝트', Icon: FolderKanban },
  { href: '/samples', label: '샘플', Icon: FlaskConical },
  { href: '/inks', label: '잉크', Icon: Beaker },
  { href: '/bases', label: '베이스', Icon: Square },
  { href: '/blends', label: '배합 계층', Icon: GitBranch },
  { href: '/match', label: '배합 추천', Icon: Wand2 },
  { href: '/import', label: 'RDP 가져오기', Icon: Database },
  { href: '/rdp', label: 'RDP-DB', Icon: Table2 },
]

export function Navbar() {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`)

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white/90 backdrop-blur">
      <nav className="max-w-7xl mx-auto px-4 flex items-center gap-1 h-14">
        <Link
          href="/"
          onClick={() => setOpen(false)}
          className="flex items-center gap-2 font-bold text-lg text-primary-700 mr-2 shrink-0"
        >
          <Palette className="w-5 h-5" />
          PCCS2
        </Link>

        {/* 데스크탑: 인라인 메뉴 */}
        <div className="hidden md:flex items-center gap-1 overflow-x-auto">
          {NAV_ITEMS.map(({ href, label, Icon }) => (
            <Link
              key={href}
              href={href}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium whitespace-nowrap transition-colors',
                isActive(href)
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}
        </div>

        {/* 모바일: 햄버거 버튼 */}
        <button
          type="button"
          onClick={() => setOpen(v => !v)}
          aria-label="메뉴 열기"
          aria-expanded={open}
          className="md:hidden ml-auto -mr-2 p-2 rounded-md text-gray-600 hover:bg-gray-100 active:bg-gray-200"
        >
          {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </nav>

      {/* 모바일: 드로어 메뉴 */}
      {open && (
        <>
          <button
            type="button"
            aria-label="메뉴 닫기"
            onClick={() => setOpen(false)}
            className="md:hidden fixed inset-x-0 bottom-0 top-14 z-30 bg-black/20"
          />
          <div className="md:hidden absolute inset-x-0 top-14 z-40 border-b border-gray-200 bg-white shadow-lg">
            <div className="grid grid-cols-2 gap-1 p-3">
              {NAV_ITEMS.map(({ href, label, Icon }) => (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setOpen(false)}
                  className={clsx(
                    'flex items-center gap-2.5 px-3 py-3 rounded-lg text-sm font-medium',
                    isActive(href)
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100 active:bg-gray-200',
                  )}
                >
                  <Icon className="w-5 h-5 shrink-0" />
                  {label}
                </Link>
              ))}
            </div>
          </div>
        </>
      )}
    </header>
  )
}
