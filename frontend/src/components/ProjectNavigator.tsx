'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/client'

interface Project {
  project_id: string
  project_name: string
  customer?: string
  status: string
}

interface Pattern {
  pattern_id: string
  pattern_name: string
  project_id: string
  status: string
}

interface Round {
  round_id: string
  round_number: number
  pattern_id: string
  work_date?: string
}

interface ProjectNavigatorProps {
  onProjectSelect?: (projectId: string) => void
  onPatternSelect?: (patternId: string) => void
  onRoundSelect?: (roundId: string) => void
  selectedProjectId?: string
  selectedPatternId?: string
  selectedRoundId?: string
}

export default function ProjectNavigator({
  onProjectSelect,
  onPatternSelect,
  onRoundSelect,
  selectedProjectId,
  selectedPatternId,
  selectedRoundId,
}: ProjectNavigatorProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [patterns, setPatterns] = useState<Pattern[]>([])
  const [rounds, setRounds] = useState<Round[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    apiClient.get<Project[]>('/api/projects/').then(setProjects)
  }, [])

  useEffect(() => {
    if (!selectedProjectId) {
      setPatterns([])
      onPatternSelect?.('')
      setRounds([])
      onRoundSelect?.('')
      return
    }
    setLoading(true)
    apiClient.get<Pattern[]>(`/api/patterns/?project_id=${selectedProjectId}`)
      .then(data => {
        setPatterns(data)
        onPatternSelect?.('')
        setRounds([])
        onRoundSelect?.('')
        setLoading(false)
      })
  }, [selectedProjectId])

  useEffect(() => {
    if (!selectedPatternId) {
      setRounds([])
      onRoundSelect?.('')
      return
    }
    setLoading(true)
    apiClient.get<Round[]>(`/api/rounds/?pattern_id=${selectedPatternId}`)
      .then(data => {
        setRounds(data)
        setLoading(false)
      })
  }, [selectedPatternId])

  return (
    <div className="grid md:grid-cols-3 gap-4">
      {/* Project Selection */}
      <div>
        <label className="block text-sm font-medium text-text-primary mb-2">
          프로젝트 *
        </label>
        <select
          value={selectedProjectId || ''}
          onChange={(e) => {
            onProjectSelect?.(e.target.value)
            if (onPatternSelect) onPatternSelect('')
            if (onRoundSelect) onRoundSelect('')
          }}
          className="w-full px-3 py-2 border border-border-subtle rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-accent-primary disabled:bg-gray-100"
          disabled={loading}
        >
          <option value="">프로젝트 선택</option>
          {projects.map((project) => (
            <option key={project.project_id} value={project.project_id}>
              {project.project_name}
            </option>
          ))}
        </select>
      </div>

      {/* Pattern Selection */}
      <div>
        <label className="block text-sm font-medium text-text-primary mb-2">
          패턴 *
        </label>
        <select
          value={selectedPatternId || ''}
          onChange={(e) => {
            onPatternSelect?.(e.target.value)
            if (onRoundSelect) onRoundSelect('')
          }}
          className="w-full px-3 py-2 border border-border-subtle rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-accent-primary disabled:bg-gray-100"
          disabled={!selectedProjectId || loading}
        >
          <option value="">패턴 선택</option>
          {patterns.map((pattern) => (
            <option key={pattern.pattern_id} value={pattern.pattern_id}>
              {pattern.pattern_name}
            </option>
          ))}
        </select>
      </div>

      {/* Round Selection */}
      <div>
        <label className="block text-sm font-medium text-text-primary mb-2">
          라운드 *
        </label>
        <select
          value={selectedRoundId || ''}
          onChange={(e) => onRoundSelect?.(e.target.value)}
          className="w-full px-3 py-2 border border-border-subtle rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-accent-primary disabled:bg-gray-100"
          disabled={!selectedPatternId || loading}
        >
          <option value="">라운드 선택</option>
          {rounds.map((round) => (
            <option key={round.round_id} value={round.round_id}>
              {round.round_number}회차 (작업일: {round.work_date || '미정'})
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
