import { ProjectCard } from './ProjectCard'
import type { Project } from '@/lib/types/project'

interface ProjectListProps {
  projects: Project[]
}

export function ProjectList({ projects }: ProjectListProps) {
  return (
    <div className="p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map((project, index) => (
          <ProjectCard key={`${project.projectId}-${index}`} project={project} />
        ))}
      </div>
    </div>
  )
}
