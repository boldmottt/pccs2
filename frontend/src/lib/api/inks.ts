import { apiClient } from './client'
import type { Ink } from '@/lib/types/project'

export interface InkCreateData {
  ink_name: string
  ink_category: 'COLOR' | 'TRANSPARENT' | 'EFFECT' | 'ADDITIVE'
  manufacturer?: string
  solid_color_sci?: { L: number; a: number; b: number }
  solid_color_sce?: { L: number; a: number; b: number }
  gloss_GU?: number
  viscosity?: number
  density?: number
  memo?: string
}

export const inksApi = {
  getAll: (params?: { category?: string; is_blend?: boolean }) => {
    const searchParams = new URLSearchParams()
    if (params?.category) searchParams.set('category', params.category)
    if (params?.is_blend !== undefined) searchParams.set('is_blend', String(params.is_blend))
    const query = searchParams.toString()
    return apiClient.get<Ink[]>(`/api/inks/${query ? `?${query}` : ''}`)
  },

  getById: (id: string) =>
    apiClient.get<Ink>(`/api/inks/${id}`),

  create: (data: InkCreateData) =>
    apiClient.post<Ink>('/api/inks/', data),

  update: (id: string, data: Partial<InkCreateData>) =>
    apiClient.put<Ink>(`/api/inks/${id}`, data),

  delete: (id: string) =>
    apiClient.delete<void>(`/api/inks/${id}`),
}
