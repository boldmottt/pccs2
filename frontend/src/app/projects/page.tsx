'use client'

import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '@/lib/api/projects'
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
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-600 mt-1">프로젝트 관리</p>
        </div>
        <Button onClick={() => router.push('/projects/new')}>
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </Button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading projects...</div>
        ) : projects && projects.length > 0 ? (
          <ProjectList projects={projects} />
        ) : (
          <div className="p-8 text-center text-gray-500">
            No projects found. Create your first project!
          </div>
        )}
      </div>
    </div>
  )
}
