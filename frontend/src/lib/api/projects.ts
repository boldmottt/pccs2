import { apiClient } from './client'
import type { Project, ProjectCreate } from '@/lib/types/project'

export const projectsApi = {
  list: () => apiClient.get<Project[]>('/api/projects/'),

  get: (projectId: string) => apiClient.get<Project>(`/api/projects/${projectId}`),

  create: (data: ProjectCreate) => apiClient.post<Project>('/api/projects/', data),

  update: (projectId: string, data: Partial<ProjectCreate>) =>
    apiClient.put<Project>(`/api/projects/${projectId}`, data),

  remove: (projectId: string) => apiClient.delete<void>(`/api/projects/${projectId}`),
}
