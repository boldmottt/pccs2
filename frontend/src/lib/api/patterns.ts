import { apiClient } from './client'
import type { Pattern, PatternCreate } from '@/lib/types/project'

export const patternsApi = {
  list: (params?: { project_id?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.project_id) searchParams.set('project_id', params.project_id)
    const query = searchParams.toString()
    return apiClient.get<Pattern[]>(`/api/patterns/${query ? `?${query}` : ''}`)
  },

  get: (patternId: string) => apiClient.get<Pattern>(`/api/patterns/${patternId}`),

  create: (data: PatternCreate) => apiClient.post<Pattern>('/api/patterns/', data),

  update: (patternId: string, data: Partial<PatternCreate>) =>
    apiClient.put<Pattern>(`/api/patterns/${patternId}`, data),

  remove: (patternId: string) => apiClient.delete<void>(`/api/patterns/${patternId}`),
}
