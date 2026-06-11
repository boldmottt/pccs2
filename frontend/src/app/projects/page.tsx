'use client'

import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '@/lib/api/projects'
import { getErrorMessage } from '@/lib/api/client'
import { ProjectList } from '@/components/projects/ProjectList'
import { HierarchyTree } from '@/components/projects/HierarchyTree'
import { Button } from '@/components/ui/Button'
import { Plus } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function ProjectsPage() {
  const router = useRouter()

  const { data: projects, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  })

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">프로젝트</h1>
          <p className="text-gray-600 mt-1">프로젝트 관리</p>
        </div>
        <Button onClick={() => router.push('/projects/new')}>
          <Plus className="w-4 h-4 mr-2" />
          새 프로젝트
        </Button>
      </div>

      <div className="grid lg:grid-cols-[300px,1fr] gap-6 items-start">
        <aside className="bg-white rounded-lg shadow-sm border border-gray-200 p-3 lg:sticky lg:top-20">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide px-2 mb-2">
            계층 구조
          </h2>
          {isLoading ? (
            <p className="text-sm text-gray-400 px-2 py-4">불러오는 중...</p>
          ) : (
            <HierarchyTree projects={projects ?? []} />
          )}
        </aside>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">프로젝트를 불러오는 중...</div>
          ) : isError ? (
            <div className="p-8 text-center">
              <p className="text-red-600 mb-4">{getErrorMessage(error)}</p>
              <Button variant="outline" onClick={() => refetch()}>
                다시 시도
              </Button>
            </div>
          ) : projects && projects.length > 0 ? (
            <ProjectList projects={projects} />
          ) : (
            <div className="p-8 text-center text-gray-500">
              프로젝트가 없습니다. 첫 프로젝트를 생성하세요.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
