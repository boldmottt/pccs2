'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { patternsApi } from '@/lib/api/patterns'
import { roundsApi } from '@/lib/api/rounds'
import { samplesApi } from '@/lib/api/samples'
import type { Pattern, Project, Round } from '@/lib/types/project'
import { ChevronRight, FolderKanban, Layers, RotateCw, FlaskConical } from 'lucide-react'
import { clsx } from 'clsx'

function NodeRow({
  depth,
  expandable,
  expanded,
  onToggle,
  href,
  icon,
  label,
  meta,
}: {
  depth: number
  expandable: boolean
  expanded?: boolean
  onToggle?: () => void
  href?: string
  icon: React.ReactNode
  label: string
  meta?: string
}) {
  const content = (
    <>
      <span
        className={clsx(
          'w-4 h-4 shrink-0 flex items-center justify-center text-gray-400',
          expandable && 'cursor-pointer hover:text-gray-700',
        )}
        onClick={e => {
          if (expandable && onToggle) {
            e.preventDefault()
            e.stopPropagation()
            onToggle()
          }
        }}
      >
        {expandable && (
          <ChevronRight className={clsx('w-3.5 h-3.5 transition-transform', expanded && 'rotate-90')} />
        )}
      </span>
      <span className="shrink-0 text-gray-400">{icon}</span>
      <span className="truncate text-sm">{label}</span>
      {meta && <span className="text-xs text-gray-400 shrink-0 ml-auto">{meta}</span>}
    </>
  )

  const className = clsx(
    'flex items-center gap-1.5 py-1 pr-2 rounded-md hover:bg-gray-100 transition-colors w-full text-left',
  )
  const style = { paddingLeft: `${depth * 14 + 4}px` }

  if (href) {
    return (
      <Link href={href} className={className} style={style}>
        {content}
      </Link>
    )
  }
  return (
    <button type="button" onClick={onToggle} className={className} style={style}>
      {content}
    </button>
  )
}

function RoundNode({ round, depth }: { round: Round; depth: number }) {
  const [expanded, setExpanded] = useState(false)

  const samplesQuery = useQuery({
    queryKey: ['samples', { round_id: round.round_id }],
    queryFn: () => samplesApi.list({ round_id: round.round_id }),
    enabled: expanded,
  })

  return (
    <div>
      <NodeRow
        depth={depth}
        expandable
        expanded={expanded}
        onToggle={() => setExpanded(v => !v)}
        icon={<RotateCw className="w-3.5 h-3.5" />}
        label={`라운드 ${round.round_number}`}
        meta={round.work_date ?? undefined}
      />
      {expanded && (
        <div>
          {samplesQuery.isLoading && (
            <p className="text-xs text-gray-400 py-1" style={{ paddingLeft: `${(depth + 1) * 14 + 24}px` }}>
              불러오는 중...
            </p>
          )}
          {(samplesQuery.data ?? []).map(sample => (
            <NodeRow
              key={sample.sample_id}
              depth={depth + 1}
              expandable={false}
              href={`/samples/${sample.sample_id}`}
              icon={<FlaskConical className="w-3.5 h-3.5" />}
              label={`샘플 ${sample.sample_number}`}
              meta={
                sample.final_delta_e !== null && sample.final_delta_e !== undefined
                  ? `ΔE ${sample.final_delta_e.toFixed(1)}`
                  : undefined
              }
            />
          ))}
          {samplesQuery.data && samplesQuery.data.length === 0 && (
            <p className="text-xs text-gray-400 py-1" style={{ paddingLeft: `${(depth + 1) * 14 + 24}px` }}>
              샘플 없음
            </p>
          )}
        </div>
      )}
    </div>
  )
}

function PatternNode({ pattern, depth }: { pattern: Pattern; depth: number }) {
  const [expanded, setExpanded] = useState(false)

  const roundsQuery = useQuery({
    queryKey: ['rounds', pattern.pattern_id],
    queryFn: () => roundsApi.list({ pattern_id: pattern.pattern_id }),
    enabled: expanded,
  })

  return (
    <div>
      <div className="flex items-center group">
        <div className="flex-1 min-w-0">
          <NodeRow
            depth={depth}
            expandable
            expanded={expanded}
            onToggle={() => setExpanded(v => !v)}
            icon={<Layers className="w-3.5 h-3.5" />}
            label={pattern.pattern_name}
          />
        </div>
        <Link
          href={`/patterns/${pattern.pattern_id}`}
          className="text-xs text-primary-600 hover:underline pr-2 opacity-0 group-hover:opacity-100 shrink-0"
        >
          열기
        </Link>
      </div>
      {expanded && (
        <div>
          {roundsQuery.isLoading && (
            <p className="text-xs text-gray-400 py-1" style={{ paddingLeft: `${(depth + 1) * 14 + 24}px` }}>
              불러오는 중...
            </p>
          )}
          {(roundsQuery.data ?? []).map(round => (
            <RoundNode key={round.round_id} round={round} depth={depth + 1} />
          ))}
          {roundsQuery.data && roundsQuery.data.length === 0 && (
            <p className="text-xs text-gray-400 py-1" style={{ paddingLeft: `${(depth + 1) * 14 + 24}px` }}>
              라운드 없음
            </p>
          )}
        </div>
      )}
    </div>
  )
}

function ProjectNode({ project }: { project: Project }) {
  const [expanded, setExpanded] = useState(false)

  const patternsQuery = useQuery({
    queryKey: ['patterns', project.project_id],
    queryFn: () => patternsApi.list({ project_id: project.project_id }),
    enabled: expanded,
  })

  return (
    <div>
      <div className="flex items-center group">
        <div className="flex-1 min-w-0">
          <NodeRow
            depth={0}
            expandable
            expanded={expanded}
            onToggle={() => setExpanded(v => !v)}
            icon={<FolderKanban className="w-3.5 h-3.5" />}
            label={project.project_name}
          />
        </div>
        <Link
          href={`/projects/${project.project_id}`}
          className="text-xs text-primary-600 hover:underline pr-2 opacity-0 group-hover:opacity-100 shrink-0"
        >
          열기
        </Link>
      </div>
      {expanded && (
        <div>
          {patternsQuery.isLoading && (
            <p className="text-xs text-gray-400 py-1 pl-10">불러오는 중...</p>
          )}
          {(patternsQuery.data ?? []).map(pattern => (
            <PatternNode key={pattern.pattern_id} pattern={pattern} depth={1} />
          ))}
          {patternsQuery.data && patternsQuery.data.length === 0 && (
            <p className="text-xs text-gray-400 py-1 pl-10">패턴 없음</p>
          )}
        </div>
      )}
    </div>
  )
}

/** Project → Pattern → Round → Sample 계층 트리 (펼칠 때 lazy 로딩) */
export function HierarchyTree({ projects }: { projects: Project[] }) {
  if (projects.length === 0) {
    return <p className="text-sm text-gray-400 px-2 py-4">프로젝트가 없습니다.</p>
  }
  return (
    <div className="space-y-0.5">
      {projects.map(project => (
        <ProjectNode key={project.project_id} project={project} />
      ))}
    </div>
  )
}
