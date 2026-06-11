'use client'

import { use, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '@/lib/api/projects'
import { patternsApi } from '@/lib/api/patterns'
import { getErrorMessage } from '@/lib/api/client'
import type { PatternCreate, Project } from '@/lib/types/project'
import { labToCss } from '@/lib/types/color'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { ArrowLeft, Pencil, Plus, Trash2, X } from 'lucide-react'

const PROJECT_STATUS_LABEL: Record<Project['status'], string> = {
  IN_PROGRESS: '진행 중',
  COMPLETED: '완료',
  ON_HOLD: '보류',
}

const PROJECT_STATUS_STYLE: Record<Project['status'], string> = {
  IN_PROGRESS: 'bg-blue-100 text-blue-800 border-blue-200',
  COMPLETED: 'bg-green-100 text-green-800 border-green-200',
  ON_HOLD: 'bg-gray-100 text-gray-800 border-gray-200',
}

interface LabFormValue {
  L: string
  a: string
  b: string
}

const EMPTY_LAB: LabFormValue = { L: '', a: '', b: '' }

function parseLab(value: LabFormValue) {
  if (value.L === '' && value.a === '' && value.b === '') return undefined
  return {
    L: Number(value.L) || 0,
    a: Number(value.a) || 0,
    b: Number(value.b) || 0,
  }
}

function LabInputs({
  label,
  value,
  onChange,
}: {
  label: string
  value: LabFormValue
  onChange: (value: LabFormValue) => void
}) {
  return (
    <div>
      <p className="text-xs text-gray-500 font-medium mb-2">{label}</p>
      <div className="grid grid-cols-3 gap-3">
        <Input
          label="L*"
          type="number"
          step="0.01"
          value={value.L}
          onChange={e => onChange({ ...value, L: e.target.value })}
        />
        <Input
          label="a*"
          type="number"
          step="0.01"
          value={value.a}
          onChange={e => onChange({ ...value, a: e.target.value })}
        />
        <Input
          label="b*"
          type="number"
          step="0.01"
          value={value.b}
          onChange={e => onChange({ ...value, b: e.target.value })}
        />
      </div>
    </div>
  )
}

function NewPatternForm({ projectId, onClose }: { projectId: string; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [patternName, setPatternName] = useState('')
  const [totalLayers, setTotalLayers] = useState('1')
  const [targetSci, setTargetSci] = useState<LabFormValue>(EMPTY_LAB)
  const [targetSce, setTargetSce] = useState<LabFormValue>(EMPTY_LAB)
  const [baseMaterial, setBaseMaterial] = useState('')
  const [nameError, setNameError] = useState<string | undefined>()

  const mutation = useMutation({
    mutationFn: (data: PatternCreate) => patternsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patterns', projectId] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!patternName.trim()) {
      setNameError('패턴 이름을 입력하세요')
      return
    }
    const payload: PatternCreate = {
      project_id: projectId,
      pattern_name: patternName.trim(),
      total_print_layers: Math.max(1, Number(totalLayers) || 1),
    }
    const sci = parseLab(targetSci)
    const sce = parseLab(targetSce)
    if (sci) payload.target_base_color_sci = sci
    if (sce) payload.target_base_color_sce = sce
    if (baseMaterial.trim()) payload.target_base_material = baseMaterial.trim()
    mutation.mutate(payload)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>새 패턴</CardTitle>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <Input
              label="패턴 이름 *"
              placeholder="예: 로고 레드"
              value={patternName}
              onChange={e => {
                setPatternName(e.target.value)
                setNameError(undefined)
              }}
              error={nameError}
            />
            <Input
              label="총 인쇄 도수"
              type="number"
              min="1"
              value={totalLayers}
              onChange={e => setTotalLayers(e.target.value)}
            />
          </div>

          <LabInputs label="목표 색상 SCI (L*, a*, b*)" value={targetSci} onChange={setTargetSci} />
          <LabInputs label="목표 색상 SCE (L*, a*, b*)" value={targetSce} onChange={setTargetSce} />

          <Input
            label="목표 베이스 소재"
            placeholder="예: ABS"
            value={baseMaterial}
            onChange={e => setBaseMaterial(e.target.value)}
          />

          {mutation.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              패턴 생성에 실패했습니다: {getErrorMessage(mutation.error)}
            </div>
          )}

          <div className="flex justify-end gap-3">
            <Button variant="outline" type="button" onClick={onClose}>
              취소
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? '생성 중...' : '패턴 생성'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

function EditProjectForm({ project, onClose }: { project: Project; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [projectName, setProjectName] = useState(project.project_name)
  const [customer, setCustomer] = useState(project.customer ?? '')
  const [status, setStatus] = useState<Project['status']>(project.status)
  const [memo, setMemo] = useState(project.memo ?? '')
  const [nameError, setNameError] = useState<string | undefined>()

  const mutation = useMutation({
    mutationFn: () =>
      projectsApi.update(project.project_id, {
        project_name: projectName.trim(),
        customer: customer.trim() || undefined,
        status,
        memo: memo.trim() || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectName.trim()) {
      setNameError('프로젝트 이름을 입력하세요')
      return
    }
    mutation.mutate()
  }

  return (
    <Card className="mb-8">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>프로젝트 수정</CardTitle>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <Input
              label="프로젝트 이름 *"
              value={projectName}
              onChange={e => {
                setProjectName(e.target.value)
                setNameError(undefined)
              }}
              error={nameError}
            />
            <Input label="고객사" value={customer} onChange={e => setCustomer(e.target.value)} />
          </div>

          <div>
            <label htmlFor="project_status" className="block text-sm font-medium text-gray-700 mb-1">
              상태
            </label>
            <select
              id="project_status"
              value={status}
              onChange={e => setStatus(e.target.value as Project['status'])}
              className="flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
            >
              {(Object.keys(PROJECT_STATUS_LABEL) as Project['status'][]).map(value => (
                <option key={value} value={value}>
                  {PROJECT_STATUS_LABEL[value]}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="project_memo" className="block text-sm font-medium text-gray-700 mb-1">
              메모
            </label>
            <textarea
              id="project_memo"
              rows={3}
              value={memo}
              onChange={e => setMemo(e.target.value)}
              className="flex w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent resize-none"
            />
          </div>

          {mutation.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              프로젝트 수정에 실패했습니다: {getErrorMessage(mutation.error)}
            </div>
          )}

          <div className="flex justify-end gap-3">
            <Button variant="outline" type="button" onClick={onClose}>
              취소
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? '저장 중...' : '저장'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

export default function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const queryClient = useQueryClient()
  const [showPatternForm, setShowPatternForm] = useState(false)
  const [editingProject, setEditingProject] = useState(false)

  const deleteMutation = useMutation({
    mutationFn: () => projectsApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      router.push('/projects')
    },
  })

  const handleDelete = () => {
    if (
      window.confirm(
        '이 프로젝트를 삭제할까요?\n프로젝트에 속한 패턴·라운드·샘플이 모두 함께 삭제됩니다.',
      )
    ) {
      deleteMutation.mutate()
    }
  }

  const projectQuery = useQuery({
    queryKey: ['projects', id],
    queryFn: () => projectsApi.get(id),
  })

  const patternsQuery = useQuery({
    queryKey: ['patterns', id],
    queryFn: () => patternsApi.list({ project_id: id }),
  })

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <Link
        href="/projects"
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 mb-6 transition-colors w-fit"
      >
        <ArrowLeft className="w-4 h-4" />
        프로젝트 목록
      </Link>

      {projectQuery.isLoading ? (
        <div className="p-8 text-center text-gray-500 bg-white rounded-lg border border-gray-200">
          프로젝트를 불러오는 중...
        </div>
      ) : projectQuery.isError ? (
        <div className="p-8 text-center bg-white rounded-lg border border-gray-200">
          <p className="text-red-600 mb-4">{getErrorMessage(projectQuery.error)}</p>
          <Button variant="outline" onClick={() => projectQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      ) : projectQuery.data ? (
        editingProject ? (
          <EditProjectForm project={projectQuery.data} onClose={() => setEditingProject(false)} />
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{projectQuery.data.project_name}</h1>
                {projectQuery.data.customer && (
                  <p className="text-gray-600 mt-1">고객사: {projectQuery.data.customer}</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium border ${PROJECT_STATUS_STYLE[projectQuery.data.status]}`}
                >
                  {PROJECT_STATUS_LABEL[projectQuery.data.status]}
                </span>
                <Button variant="outline" size="sm" onClick={() => setEditingProject(true)}>
                  <Pencil className="w-3.5 h-3.5 mr-1" />
                  수정
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDelete}
                  disabled={deleteMutation.isPending}
                  className="text-red-600 border-red-200 hover:bg-red-50"
                >
                  <Trash2 className="w-3.5 h-3.5 mr-1" />
                  삭제
                </Button>
              </div>
            </div>
            {projectQuery.data.memo && (
              <p className="text-sm text-gray-500 mt-4 whitespace-pre-wrap">{projectQuery.data.memo}</p>
            )}
          </div>
        )
      ) : null}

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">패턴</h2>
        {!showPatternForm && (
          <Button onClick={() => setShowPatternForm(true)}>
            <Plus className="w-4 h-4 mr-1" />새 패턴
          </Button>
        )}
      </div>

      {showPatternForm && (
        <div className="mb-6">
          <NewPatternForm projectId={id} onClose={() => setShowPatternForm(false)} />
        </div>
      )}

      {patternsQuery.isLoading ? (
        <div className="p-8 text-center text-gray-500 bg-white rounded-lg border border-gray-200">
          패턴을 불러오는 중...
        </div>
      ) : patternsQuery.isError ? (
        <div className="p-8 text-center bg-white rounded-lg border border-gray-200">
          <p className="text-red-600 mb-4">{getErrorMessage(patternsQuery.error)}</p>
          <Button variant="outline" onClick={() => patternsQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      ) : patternsQuery.data && patternsQuery.data.length > 0 ? (
        <div className="grid sm:grid-cols-2 gap-4">
          {patternsQuery.data.map(pattern => (
            <Link key={pattern.pattern_id} href={`/patterns/${pattern.pattern_id}`} className="block">
              <Card className="hover:shadow-md transition-shadow h-full">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    {pattern.target_base_color_sci && (
                      <div
                        className="w-10 h-10 rounded-lg border border-gray-200 shrink-0"
                        style={{ backgroundColor: labToCss(pattern.target_base_color_sci) }}
                      />
                    )}
                    <div className="min-w-0">
                      <h3 className="font-semibold truncate">{pattern.pattern_name}</h3>
                      <p className="text-sm text-gray-500">
                        {pattern.total_print_layers}도 인쇄
                        {pattern.target_base_material ? ` · ${pattern.target_base_material}` : ''}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <div className="p-8 text-center text-gray-500 bg-white rounded-lg border border-gray-200">
          등록된 패턴이 없습니다.
        </div>
      )}
    </div>
  )
}
