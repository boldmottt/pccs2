'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '@/lib/api/projects'
import { samplesApi } from '@/lib/api/samples'
import { inksApi } from '@/lib/api/inks'
import { SuccessFlagBadge } from '@/components/samples/SuccessFlagBadge'
import { FolderKanban, Beaker, FlaskConical, Wand2, Database, Square } from 'lucide-react'

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
    href: '/bases',
    title: '베이스',
    description: '베이스(소재·도장) 마스터',
    Icon: Square,
  },
  {
    href: '/match',
    title: '배합 추천',
    description: 'AI 기반 잉크 배합비 추천',
    Icon: Wand2,
  },
  {
    href: '/import',
    title: 'RDP-DB 가져오기',
    description: '작업일지 배합비 DB 일괄 등록',
    Icon: Database,
  },
]

function StatValue({ value, isLoading }: { value: number | undefined; isLoading: boolean }) {
  if (isLoading) return <span className="inline-block w-8 h-7 bg-gray-100 rounded animate-pulse" />
  return <>{value ?? '-'}</>
}

export default function Home() {
  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: () => projectsApi.list() })
  const samplesQuery = useQuery({ queryKey: ['samples'], queryFn: () => samplesApi.list() })
  const inksQuery = useQuery({ queryKey: ['inks'], queryFn: () => inksApi.list() })

  const samples = samplesQuery.data ?? []
  const successCount = samples.filter(s => s.success_flag === 'SUCCESS').length
  const recentSamples = [...samples]
    .sort((a, b) => (b.created_at > a.created_at ? 1 : -1))
    .slice(0, 5)

  const stats = [
    { label: '프로젝트', value: projectsQuery.data?.length, isLoading: projectsQuery.isLoading },
    { label: '샘플', value: samples.length, isLoading: samplesQuery.isLoading },
    { label: '성공 샘플', value: successCount, isLoading: samplesQuery.isLoading },
    { label: '잉크', value: inksQuery.data?.length, isLoading: inksQuery.isLoading },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold mb-4">PCCS2</h1>
        <p className="text-xl text-gray-600">
          빅데이터 기반 AI 잉크 배합비 추천 시스템
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
        {stats.map(stat => (
          <div
            key={stat.label}
            className="rounded-lg border border-gray-200 bg-white p-5 text-center"
          >
            <p className="text-3xl font-bold text-primary-700">
              <StatValue value={stat.value} isLoading={stat.isLoading} />
            </p>
            <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-6 mb-12">
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

      {recentSamples.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">최근 샘플</h2>
          <div className="divide-y divide-gray-100">
            {recentSamples.map(sample => (
              <Link
                key={sample.sample_id}
                href={`/samples/${sample.sample_id}`}
                className="flex items-center justify-between py-2.5 hover:bg-gray-50 px-2 -mx-2 rounded-lg transition-colors"
              >
                <span className="font-medium text-sm">
                  샘플 {sample.sample_number}
                  <span className="text-gray-400 font-normal ml-2">{sample.base_material}</span>
                </span>
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-gray-500">
                    ΔE:{' '}
                    {sample.final_delta_e !== null && sample.final_delta_e !== undefined
                      ? sample.final_delta_e.toFixed(2)
                      : '-'}
                  </span>
                  <SuccessFlagBadge flag={sample.success_flag} />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
