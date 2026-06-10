import { apiClient } from './client'
import type { Round, RoundCreate } from '@/lib/types/project'

export const roundsApi = {
  list: (params?: { pattern_id?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.pattern_id) searchParams.set('pattern_id', params.pattern_id)
    const query = searchParams.toString()
    return apiClient.get<Round[]>(`/api/rounds/${query ? `?${query}` : ''}`)
  },

  get: (roundId: string) => apiClient.get<Round>(`/api/rounds/${roundId}`),

  /** round_number는 백엔드에서 자동 부여 */
  create: (patternId: string, data?: RoundCreate) =>
    apiClient.post<Round>(`/api/rounds/pattern/${patternId}`, data ?? {}),

  update: (roundId: string, data: Partial<RoundCreate>) =>
    apiClient.put<Round>(`/api/rounds/${roundId}`, data),

  remove: (roundId: string) => apiClient.delete<void>(`/api/rounds/${roundId}`),
}
