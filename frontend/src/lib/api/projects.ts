import { apiClient } from './client'
import type { Project } from '@/lib/types/project'

export const projectsApi = {
  getAll: () => apiClient.get<Project[]>('/api/projects'),

  getById: (id: string) =>
    apiClient.get<Project>(`/api/projects/${id}`),

  create: (data: Omit<Project, 'projectId' | 'createdAt' | 'updatedAt'>) =>
    apiClient.post<Project>('/api/projects', data),

  update: (id: string, data: Partial<Project>) =>
    apiClient.put<Project>(`/api/projects/${id}`, data),

  delete: (id: string) =>
    apiClient.delete<void>(`/api/projects/${id}`),
}
