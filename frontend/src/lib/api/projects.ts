import { apiClient } from './client'
import type { Project } from '@/lib/types/project'

export interface ProjectCreate {
  project_name: string
  customer?: string
  start_date?: string
  target_completion?: string
  memo?: string
}

export interface ProjectUpdate {
  project_name?: string
  customer?: string
  status?: string
  target_completion?: string
  memo?: string
}

export interface ProjectResponse {
  project_id: string
  project_name: string
  customer?: string
  status: 'IN_PROGRESS' | 'COMPLETED' | 'ON_HOLD'
  start_date?: string
  target_completion?: string
  memo?: string
  created_at: string
  updated_at: string
}

export const projectsApi = {
  getAll: () => apiClient.get<ProjectResponse[]>('/api/projects'),

  getById: (id: string) =>
    apiClient.get<ProjectResponse>(`/api/projects/${id}`),

  create: (data: ProjectCreate) =>
    apiClient.post<ProjectResponse>('/api/projects', data),

  update: (id: string, data: ProjectUpdate) =>
    apiClient.put<ProjectResponse>(`/api/projects/${id}`, data),

  delete: (id: string) =>
    apiClient.delete<void>(`/api/projects/${id}`),
}
