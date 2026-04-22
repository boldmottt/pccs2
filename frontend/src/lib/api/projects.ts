import { apiClient } from './client'
import type { Project } from '@/lib/types/project'

export interface ProjectCreate {
  projectName: string
  customer?: string
  startDate?: string
  targetCompletion?: string
  memo?: string
}

export interface ProjectUpdate {
  projectName?: string
  customer?: string
  status?: string
  targetCompletion?: string
  memo?: string
}

export interface ProjectResponse {
  projectId: string
  projectName: string
  customer?: string
  status: 'IN_PROGRESS' | 'COMPLETED' | 'ON_HOLD'
  startDate?: string
  targetCompletion?: string
  memo?: string
  createdAt: string
  updatedAt: string
}

export const projectsApi = {
  getAll: () => apiClient.get<ProjectResponse[]>('/api/projects'),

  getById: (id: string) =>
    apiClient.get<ProjectResponse>(`/api/projects/${id}`),

  create: (data: ProjectCreate) =>
    apiClient.post<ProjectResponse>('/api/projects', data),

  update: (params: { id: string; data: ProjectUpdate }) =>
    apiClient.put<ProjectResponse>(`/api/projects/${params.id}`, params.data),

  delete: (id: string) =>
    apiClient.delete<void>(`/api/projects/${id}`),
}
