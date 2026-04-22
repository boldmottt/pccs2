import { apiClient } from './client'
import type { Ink } from '@/lib/types/project'

export const inksApi = {
  getAll: (category?: string) =>
    apiClient.get<Ink[]>(`/api/inks/${category ? `?category=${category}` : ''}`),
  getById: (id: string) =>
    apiClient.get<Ink>(`/api/inks/${id}`),
  create: (data: any) =>
    apiClient.post<Ink>('/api/inks/', data),
  update: (id: string, data: any) =>
    apiClient.put<Ink>(`/api/inks/${id}`, data),
  delete: (id: string) =>
    apiClient.delete<void>(`/api/inks/${id}`),
}
