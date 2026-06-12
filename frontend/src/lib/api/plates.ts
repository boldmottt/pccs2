import { apiClient } from './client'
import type { Plate, PlateCreate } from '@/lib/types/project'

export const platesApi = {
  list: (params?: { pattern_id?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.pattern_id) searchParams.set('pattern_id', params.pattern_id)
    const query = searchParams.toString()
    return apiClient.get<Plate[]>(`/api/plates/${query ? `?${query}` : ''}`)
  },

  get: (plateId: string) => apiClient.get<Plate>(`/api/plates/${plateId}`),

  create: (data: PlateCreate) => apiClient.post<Plate>('/api/plates/', data),

  update: (plateId: string, data: Partial<Omit<PlateCreate, 'pattern_id'>>) =>
    apiClient.put<Plate>(`/api/plates/${plateId}`, data),

  remove: (plateId: string) => apiClient.delete<void>(`/api/plates/${plateId}`),
}
