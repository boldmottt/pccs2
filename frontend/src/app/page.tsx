import Link from 'next/link'
import { FolderKanban, Beaker, FlaskConical, Wand2 } from 'lucide-react'

const NAV_CARDS = [
  {
    href: '/projects',
    title: '프로젝트',
    description: '프로젝트 및 패턴 관리',
    Icon: FolderKanban,
  },
  {
    href: '/inks',
    title: '잉크',
    description: '잉크 마스터 데이터',
    Icon: Beaker,
  },
  {
    href: '/samples',
    title: '샘플',
    description: '샘플 배합비 관리',
    Icon: FlaskConical,
  },
  {
    href: '/match',
    title: '배합 추천',
    description: 'AI 기반 잉크 배합비 추천',
    Icon: Wand2,
  },
]

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">PCCS2</h1>
        <p className="text-xl text-gray-600">
          빅데이터 기반 AI 잉크 배합비 추천 시스템
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {NAV_CARDS.map(({ href, title, description, Icon }) => (
          <Link key={href} href={href} className="block">
            <div className="rounded-lg border border-gray-200 bg-white p-6 hover:shadow-lg transition-shadow h-full">
              <Icon className="w-8 h-8 text-primary-600 mb-3" />
              <h3 className="text-xl font-semibold mb-2">{title}</h3>
              <p className="text-gray-600">{description}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
