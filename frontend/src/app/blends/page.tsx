'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '@/lib/api/projects'
import { patternsApi } from '@/lib/api/patterns'
import { platesApi } from '@/lib/api/plates'
import { inksApi } from '@/lib/api/inks'
import { getErrorMessage } from '@/lib/api/client'
import type { Ink, Pattern, Plate, Project } from '@/lib/types/project'
import { labToCss } from '@/lib/types/color'
import { Button } from '@/components/ui/Button'
import {
  ChevronRight,
  FolderKanban,
  Layers,
  Stamp,
  Droplets,
  GitBranch,
} from 'lucide-react'
import { clsx } from 'clsx'

function Row({
  depth,
  expandable,
  expanded,
  onToggle,
  icon,
  label,
  meta,
  swatch,
}: {
  depth: number
  expandable?: boolean
  expanded?: boolean
  onToggle?: () => void
  icon: React.ReactNode
  label: React.ReactNode
  meta?: string
  swatch?: string
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={clsx(
        'flex items-center gap-1.5 py-1.5 pr-2 rounded-md w-full text-left transition-colors',
        expandable ? 'hover:bg-gray-100' : 'cursor-default',
      )}
      style={{ paddingLeft: `${depth * 16 + 4}px` }}
    >
      <span className="w-4 h-4 shrink-0 flex items-center justify-center text-gray-400">
        {expandable && (
          <ChevronRight
            className={clsx('w-3.5 h-3.5 transition-transform', expanded && 'rotate-90')}
          />
        )}
      </span>
      {swatch && (
        <span
          className="w-3.5 h-3.5 rounded border border-gray-200 shrink-0"
          style={{ backgroundColor: swatch }}
        />
      )}
      <span className="shrink-0 text-gray-400">{icon}</span>
      <span className="truncate text-sm">{label}</span>
      {meta && <span className="text-xs text-gray-400 shrink-0 ml-auto">{meta}</span>}
    </button>
  )
}

function BlendRow({ blend, depth }: { blend: Ink; depth: number }) {
  const recipe = blend.blend_recipe as { ink_items?: Array<{ amount: number }> } | null
  const itemCount = recipe?.ink_items?.length ?? 0
  return (
    <Row
      depth={depth}
      icon={<Droplets className="w-3.5 h-3.5" />}
      label={blend.ink_name}
      meta={itemCount > 0 ? `${itemCount}성분` : undefined}
      swatch={blend.solid_color_sci ? labToCss(blend.solid_color_sci) : undefined}
    />
  )
}

function PlateNode({
  plate,
  blends,
  depth,
}: {
  plate: Plate
  blends: Ink[]
  depth: number
}) {
  const [expanded, setExpanded] = useState(false)
  const bound = blends.filter(b => b.plate_id === plate.plate_id)

  return (
    <div>
      <Row
        depth={depth}
        expandable
        expanded={expanded}
        onToggle={() => setExpanded(v => !v)}
        icon={<Stamp className="w-3.5 h-3.5" />}
        label={plate.plate_code}
        meta={`배합 ${bound.length}`}
      />
      {expanded &&
        (bound.length > 0 ? (
          bound.map(blend => <BlendRow key={blend.ink_id} blend={blend} depth={depth + 1} />)
        ) : (
          <p
            className="text-xs text-gray-400 py-1"
            style={{ paddingLeft: `${(depth + 1) * 16 + 24}px` }}
          >
            이 동판에 종속된 배합 없음
          </p>
        ))}
    </div>
  )
}

function PatternNode({
  pattern,
  blends,
  depth,
}: {
  pattern: Pattern
  blends: Ink[]
  depth: number
}) {
  const [expanded, setExpanded] = useState(false)

  const platesQuery = useQuery({
    queryKey: ['plates', pattern.pattern_id],
    queryFn: () => platesApi.list({ pattern_id: pattern.pattern_id }),
    enabled: expanded,
  })

  return (
    <div>
      <Row
        depth={depth}
        expandable
        expanded={expanded}
        onToggle={() => setExpanded(v => !v)}
        icon={<Layers className="w-3.5 h-3.5" />}
        label={pattern.pattern_name}
      />
      {expanded && (
        <div>
          {platesQuery.isLoading && (
            <p
              className="text-xs text-gray-400 py-1"
              style={{ paddingLeft: `${(depth + 1) * 16 + 24}px` }}
            >
              동판을 불러오는 중...
            </p>
          )}
          {(platesQuery.data ?? []).map(plate => (
            <PlateNode key={plate.plate_id} plate={plate} blends={blends} depth={depth + 1} />
          ))}
          {platesQuery.data && platesQuery.data.length === 0 && (
            <p
              className="text-xs text-gray-400 py-1"
              style={{ paddingLeft: `${(depth + 1) * 16 + 24}px` }}
            >
              등록된 동판 없음 — 패턴 상세에서 동판을 추가하세요
            </p>
          )}
        </div>
      )}
    </div>
  )
}

function ProjectNode({ project, blends }: { project: Project; blends: Ink[] }) {
  const [expanded, setExpanded] = useState(false)

  const patternsQuery = useQuery({
    queryKey: ['patterns', project.project_id],
    queryFn: () => patternsApi.list({ project_id: project.project_id }),
    enabled: expanded,
  })

  return (
    <div>
      <Row
        depth={0}
        expandable
        expanded={expanded}
        onToggle={() => setExpanded(v => !v)}
        icon={<FolderKanban className="w-3.5 h-3.5" />}
        label={<span className="font-medium">{project.project_name}</span>}
      />
      {expanded && (
        <div>
          {patternsQuery.isLoading && (
            <p className="text-xs text-gray-400 py-1 pl-11">패턴을 불러오는 중...</p>
          )}
          {(patternsQuery.data ?? []).map(pattern => (
            <PatternNode key={pattern.pattern_id} pattern={pattern} blends={blends} depth={1} />
          ))}
          {patternsQuery.data && patternsQuery.data.length === 0 && (
            <p className="text-xs text-gray-400 py-1 pl-11">패턴 없음</p>
          )}
        </div>
      )}
    </div>
  )
}

export default function BlendsPage() {
  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: () => projectsApi.list() })
  const blendsQuery = useQuery({
    queryKey: ['inks', 'blends'],
    queryFn: () => inksApi.list({ is_blend: true }),
  })

  const blends = blendsQuery.data ?? []
  const independent = blends.filter(b => !b.plate_id)

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-2">
        <GitBranch className="w-7 h-7 text-primary-600" />
        <h1 className="text-3xl font-bold text-gray-900">배합 계층</h1>
      </div>
      <p className="text-gray-600 mb-8">
        차종 → 패턴 → 동판 → 배합비 계층과 어디에도 종속되지 않은 독립 배합을 구분해 보여줍니다.
        배합은 샘플 작성 화면의 &quot;마스터 잉크로 등록&quot;에서 동판을 선택해 종속시킬 수 있습니다.
      </p>

      {(projectsQuery.isError || blendsQuery.isError) && (
        <div className="p-6 mb-6 text-center bg-white rounded-lg border border-gray-200">
          <p className="text-red-600 mb-3">
            {getErrorMessage(projectsQuery.error ?? blendsQuery.error)}
          </p>
          <Button
            variant="outline"
            onClick={() => {
              projectsQuery.refetch()
              blendsQuery.refetch()
            }}
          >
            다시 시도
          </Button>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide px-2 mb-2">
          동판 종속 배합
        </h2>
        {projectsQuery.isLoading || blendsQuery.isLoading ? (
          <p className="text-sm text-gray-400 px-2 py-4">불러오는 중...</p>
        ) : (projectsQuery.data ?? []).length > 0 ? (
          <div className="space-y-0.5">
            {(projectsQuery.data ?? []).map(project => (
              <ProjectNode key={project.project_id} project={project} blends={blends} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400 px-2 py-4">프로젝트가 없습니다.</p>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide px-2 mb-2">
          독립 배합 (동판 미종속)
        </h2>
        {blendsQuery.isLoading ? (
          <p className="text-sm text-gray-400 px-2 py-4">불러오는 중...</p>
        ) : independent.length > 0 ? (
          <div className="space-y-0.5">
            {independent.map(blend => (
              <BlendRow key={blend.ink_id} blend={blend} depth={0} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400 px-2 py-4">독립 배합이 없습니다.</p>
        )}
      </div>

      <p className="text-sm text-gray-400 mt-4">
        배합 수정·삭제는{' '}
        <Link href="/inks" className="text-primary-600 hover:underline">
          잉크 페이지
        </Link>
        에서 할 수 있습니다.
      </p>
    </div>
  )
}
