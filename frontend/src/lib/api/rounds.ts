import { apiClient } from './client'

export const roundsApi = {
  getAll: (patternId?: string) => {
    const qs = patternId ? `?pattern_id=${patternId}` : ''
    return apiClient.get<any[]>(`/api/rounds/${qs}`)
  },
  getById: (id: string) => apiClient.get<any>(`/api/rounds/${id}`),
  create: (patternId: string, data: any) => apiClient.post<any>(`/api/rounds/pattern/${patternId}`, data),
  update: (id: string, data: any) => apiClient.put<any>(`/api/rounds/${id}`, data),
  delete: (id: string) => apiClient.delete<void>(`/api/rounds/${id}`),
}
