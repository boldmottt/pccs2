import { apiClient } from './client'
import type { Sample } from '@/lib/types/project'

export const samplesApi = {
  getAll: (params?: { patternId?: string; roundId?: string }) => {
    const query = new URLSearchParams()
    if (params?.patternId) query.set('pattern_id', params.patternId)
    if (params?.roundId) query.set('round_id', params.roundId)
    const qs = query.toString()
    return apiClient.get<Sample[]>(`/api/samples/${qs ? `?${qs}` : ''}`)
  },
  getById: (id: string) =>
    apiClient.get<Sample>(`/api/samples/${id}`),
  create: (roundId: string, data: any) =>
    apiClient.post<Sample>(`/api/samples/round/${roundId}`, data),
  update: (id: string, data: any) =>
    apiClient.put<Sample>(`/api/samples/${id}`, data),
  delete: (id: string) =>
    apiClient.delete<void>(`/api/samples/${id}`),
}
