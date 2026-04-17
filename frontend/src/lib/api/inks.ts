import { apiClient } from './client'
import type { Ink } from '@/lib/types/project'

export type InkCategory = 'COLOR' | 'TRANSPARENT' | 'EFFECT' | 'ADDITIVE'

export interface InkCreate {
  ink_name: string
  ink_category?: InkCategory
  manufacturer?: string
  solid_color_sci?: { L: number; a: number; b: number }
  solid_color_sce?: { L: number; a: number; b: number }
  gloss_GU?: number
  viscosity?: number
  density?: number
  memo?: string
}

export interface InkResponse {
  ink_id: string
  ink_name: string
  ink_category: string
  manufacturer?: string
  is_blend_ink: boolean
  blend_recipe?: any
  solid_color_sci?: { L: number; a: number; b: number }
  solid_color_sce?: { L: number; a: number; b: number }
  gloss_GU?: number
  viscosity?: number
  density?: number
  memo?: string
  registered_at: string
  updated_at: string
}

export const inksApi = {
  getAll: (category?: string, isBlend?: boolean) =>
    apiClient.get<InkResponse[]>(`/api/inks${category ? `?category=${category}` : ''}${isBlend ? `&is_blend=${isBlend}` : ''}`),

  getById: (id: string) =>
    apiClient.get<InkResponse>(`/api/inks/${id}`),

  create: (data: InkCreate) =>
    apiClient.post<InkResponse>('/api/inks', data),

  update: (id: string, data: Partial<InkCreate>) =>
    apiClient.put<InkResponse>(`/api/inks/${id}`, data),

  delete: (id: string) =>
    apiClient.delete<void>(`/api/inks/${id}`),
}
