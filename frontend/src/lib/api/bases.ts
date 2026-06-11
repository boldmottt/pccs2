import { apiClient } from './client'
import type { BaseMaster, BaseMasterCreate } from '@/lib/types/project'

export const basesApi = {
  list: (params?: { q?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.q) searchParams.set('q', params.q)
    const query = searchParams.toString()
    return apiClient.get<BaseMaster[]>(`/api/bases/${query ? `?${query}` : ''}`)
  },

  get: (baseId: string) => apiClient.get<BaseMaster>(`/api/bases/${baseId}`),

  create: (data: BaseMasterCreate) => apiClient.post<BaseMaster>('/api/bases/', data),

  update: (baseId: string, data: Partial<BaseMasterCreate>) =>
    apiClient.put<BaseMaster>(`/api/bases/${baseId}`, data),

  remove: (baseId: string) => apiClient.delete<void>(`/api/bases/${baseId}`),
}
