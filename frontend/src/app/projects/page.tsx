'use client'

import { useQuery } from '@tanstack/react-query'
import { projectsApi, type ProjectResponse } from '@/lib/api/projects'
import { ProjectList } from '@/components/projects/ProjectList'
import { Button } from '@/components/ui/Button'
import { Plus } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function ProjectsPage() {
  const router = useRouter()

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2">Projects</h1>
          <p className="text-text-secondary">프로젝트 관리</p>
        </div>
        <Button onClick={() => router.push('/projects/new')}>
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </Button>
      </div>

      {/* Content Card */}
      <div className="bg-bg-secondary/50 backdrop-blur-sm border border-border-subtle rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-text-secondary">로딩 중...</div>
        ) : projects && projects.length > 0 ? (
          <ProjectList projects={projects as any} />
        ) : (
          <div className="p-16 text-center">
            <p className="text-text-secondary text-lg">
              프로젝트가 없습니다. 첫 번째 프로젝트를 생성하세요!
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
