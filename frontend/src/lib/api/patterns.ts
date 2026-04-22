import { apiClient } from './client'

export const patternsApi = {
  getAll: (projectId?: string) => {
    const qs = projectId ? `?project_id=${projectId}` : ''
    return apiClient.get<any[]>(`/api/patterns/${qs}`)
  },
  getById: (id: string) => apiClient.get<any>(`/api/patterns/${id}`),
  create: (data: any) => apiClient.post<any>('/api/patterns/', data),
  update: (id: string, data: any) => apiClient.put<any>(`/api/patterns/${id}`, data),
  delete: (id: string) => apiClient.delete<void>(`/api/patterns/${id}`),
}
