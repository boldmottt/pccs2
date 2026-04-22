import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import type { Project } from '@/lib/types/project'
import { useRouter } from 'next/navigation'
import { Edit2, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Input } from '@/components/ui/Input'

interface ProjectCardProps {
  project: Project
}

export function ProjectCard({ project }: ProjectCardProps) {
  const router = useRouter()
  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState({
    project_name: project.projectName,
    customer: project.customer || '',
    target_completion: project.targetCompletion || '',
    memo: project.memo || '',
  })

  const getStatusColor = (status: Project['status']) => {
    switch (status) {
      case 'IN_PROGRESS':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'COMPLETED':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'ON_HOLD':
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const handleEdit = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/projects/${project.projectId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editData),
      })
      if (!response.ok) throw new Error('Failed to update project')
      setIsEditing(false)
      window.location.reload()
    } catch (error) {
      console.error('Failed to update project:', error)
      alert('프로젝트 수정에 실패했습니다.')
    }
  }

  const handleDelete = async () => {
    if (!confirm('정말 이 프로젝트를 삭제하시겠습니까?')) return
    try {
      const response = await fetch(`http://localhost:8000/api/projects/${project.projectId}`, {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('Failed to delete project')
      window.location.reload()
    } catch (error) {
      console.error('Failed to delete project:', error)
      alert('프로젝트 삭제에 실패했습니다.')
    }
  }

  if (isEditing) {
    return (
      <Card className="hover:shadow-md transition-shadow">
        <CardHeader>
          <CardTitle className="text-xl">프로젝트 수정</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">프로젝트 이름</label>
            <Input
              value={editData.project_name}
              onChange={(e) => setEditData({ ...editData, project_name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">고객사</label>
            <Input
              value={editData.customer}
              onChange={(e) => setEditData({ ...editData, customer: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">예상 완료일</label>
            <Input
              type="date"
              value={editData.target_completion || ''}
              onChange={(e) => setEditData({ ...editData, target_completion: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">메모</label>
            <textarea
              value={editData.memo}
              onChange={(e) => setEditData({ ...editData, memo: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex gap-2">
            <Button onClick={handleEdit}>저장</Button>
            <Button variant="outline" onClick={() => setIsEditing(false)}>취소</Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <CardTitle className="text-xl">{project.projectName}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between gap-2">
          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(project.status)}`}>
            {project.status === 'IN_PROGRESS' ? '진행 중' :
             project.status === 'COMPLETED' ? '완료' :
             '보류'}
          </span>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push(`/projects/${project.projectId}`)}
            >
              세부정보
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(true)}
              className="text-blue-600"
            >
              <Edit2 className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDelete}
              className="text-red-600"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="text-sm text-gray-500">
          <div>생성일: {formatDate(project.createdAt)}</div>
        </div>
      </CardContent>
    </Card>
  )
}
