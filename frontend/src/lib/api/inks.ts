import { apiClient } from './client'
import type { Ink, InkCreate } from '@/lib/types/project'

export const inksApi = {
  list: (params?: { category?: string; is_blend?: boolean }) => {
    const searchParams = new URLSearchParams()
    if (params?.category) searchParams.set('category', params.category)
    if (params?.is_blend !== undefined) searchParams.set('is_blend', String(params.is_blend))
    const query = searchParams.toString()
    return apiClient.get<Ink[]>(`/api/inks/${query ? `?${query}` : ''}`)
  },

  get: (inkId: string) => apiClient.get<Ink>(`/api/inks/${inkId}`),

  create: (data: InkCreate) => apiClient.post<Ink>('/api/inks/', data),

  update: (inkId: string, data: Partial<InkCreate>) =>
    apiClient.put<Ink>(`/api/inks/${inkId}`, data),

  remove: (inkId: string) => apiClient.delete<void>(`/api/inks/${inkId}`),

  /** 배합 잉크를 마스터 잉크로 등록 (스펙 3.2). 잉크가 없으면 새로 생성 */
  registerBlend: (
    inkId: string,
    data?: {
      ink_name?: string
      ink_category?: string
      manufacturer?: string
      blend_recipe?: Record<string, unknown>
    },
  ) => apiClient.post<Ink>(`/api/inks/${inkId}/register-blend`, data ?? {}),
}
