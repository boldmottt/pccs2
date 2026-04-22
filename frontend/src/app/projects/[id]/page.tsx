'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter, useParams } from 'next/navigation'
import { projectsApi } from '@/lib/api/projects'
import { patternsApi } from '@/lib/api/patterns'
import { Button } from '@/components/ui/Button'

export default function ProjectDetailPage() {
  const router = useRouter()
  const params = useParams()
  const queryClient = useQueryClient()
  const projectId = params.id as string

  const { data: project, isLoading, error } = useQuery({
    queryKey: ['projects', projectId],
    queryFn: () => projectsApi.getById(projectId),
  })

  const { data: patterns = [] } = useQuery({
    queryKey: ['patterns', { projectId }],
    queryFn: () => patternsApi.getAll(projectId),
  })

  const updateMutation = useMutation({
    mutationFn: projectsApi.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: projectsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      router.push('/projects')
    },
  })

  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState({
    projectName: '',
    customer: '',
    status: 'IN_PROGRESS',
    memo: '',
  })

  if (isLoading) return <div className="p-8">로딩 중...</div>
  if (error) return <div className="p-8 text-red-500">에러: {error.message}</div>
  if (!project) return <div className="p-8">프로젝트를 찾을 수 없습니다.</div>

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate({
      id: projectId,
      data: editData,
    })
    setIsEditing(false)
  }

  const handleDelete = () => {
    if (confirm('정말 삭제하시겠습니까?')) {
      deleteMutation.mutate(projectId)
    }
  }

  const handleAddPattern = () => {
    const patternName = prompt('패턴 이름:')
    if (!patternName) return
    const totalLayers = parseInt(prompt('총 인쇄 레이어 수 (1-10):') || '1')
    if (isNaN(totalLayers) || totalLayers < 1 || totalLayers > 10) {
      alert('1-10 사이의 숫자를 입력하세요')
      return
    }
    const targetMaterial = prompt('기본 재료 (선택):')

    patternsApi.create({
      projectId,
      patternName,
      totalPrintLayers: totalLayers,
      targetBaseMaterial: targetMaterial || undefined,
    }).then(() => {
      queryClient.invalidateQueries({ queryKey: ['patterns', { projectId }] })
    })
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">프로젝트 상세</h1>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          {isEditing ? (
            <form onSubmit={handleUpdate} className="space-y-4 w-full">
              <div>
                <label className="block text-sm font-medium mb-1">프로젝트명</label>
                <input
                  type="text"
                  value={editData.projectName}
                  onChange={e => setEditData(prev => ({ ...prev, projectName: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">고객사</label>
                <input
                  type="text"
                  value={editData.customer}
                  onChange={e => setEditData(prev => ({ ...prev, customer: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">상태</label>
                <select
                  value={editData.status}
                  onChange={e => setEditData(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="IN_PROGRESS">진행 중</option>
                  <option value="COMPLETED">완료</option>
                  <option value="ON_HOLD">보류</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">메모</label>
                <textarea
                  value={editData.memo}
                  onChange={e => setEditData(prev => ({ ...prev, memo: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2"
                  rows={3}
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={updateMutation.isPending}>
                  저장
                </Button>
                <Button type="button" variant="outline" onClick={() => setIsEditing(false)}>
                  취소
                </Button>
              </div>
            </form>
          ) : (
            <>
              <div>
                <h2 className="text-2xl font-bold">{project.projectName}</h2>
                <p className="text-gray-600">고객사: {project.customer || '없음'}</p>
                <p className="text-gray-600">상태: {project.status}</p>
              </div>
              <div className="flex gap-2">
                <Button onClick={() => setIsEditing(true)}>수정</Button>
                <Button variant="outline" onClick={handleDelete} className="text-red-500">
                  삭제
                </Button>
              </div>
            </>
          )}
        </div>
        {isEditing && updateMutation.isError && (
          <p className="text-red-500 text-sm">수정 실패: {updateMutation.error.message}</p>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">패턴 목록</h2>
          <Button onClick={handleAddPattern}>패턴 추가</Button>
        </div>
        <div className="space-y-2">
          {patterns.map((pattern: any) => (
            <div key={pattern.patternId} className="border rounded-lg p-4">
              <h3 className="font-semibold">{pattern.patternName}</h3>
              <p className="text-sm text-gray-600">레이이어: {pattern.totalPrintLayers}</p>
            </div>
          ))}
          {patterns.length === 0 && <p className="text-gray-500">패턴이 없습니다.</p>}
        </div>
      </div>
    </div>
  )
}
