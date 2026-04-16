import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import type { Project } from '@/lib/types/project'
import { useRouter } from 'next/navigation'

interface ProjectCardProps {
  project: Project
}

export function ProjectCard({ project }: ProjectCardProps) {
  const router = useRouter()

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

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <CardTitle className="text-xl">{project.projectName}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(project.status)}`}>
            {project.status === 'IN_PROGRESS' ? '진행 중' :
             project.status === 'COMPLETED' ? '완료' :
             '보류'}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push(`/projects/${project.projectId}`)}
          >
            세부정보
          </Button>
        </div>

        <div className="text-sm text-gray-500">
          <div>생성일: {formatDate(project.createdAt)}</div>
        </div>
      </CardContent>
    </Card>
  )
}
