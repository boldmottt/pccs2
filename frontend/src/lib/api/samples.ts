import { apiClient } from './client'
import type { Layer, InkItem } from '@/lib/types/project'

export interface SampleCreate {
  round_id: string
  sample_number: number
  base_color_sci: { L: number; a: number; b: number }
  base_color_sce: { L: number; a: number; b: number }
  base_material: string
  layers: Array<{
    layer_number: number
    ink_items: { ink_id: string; amount: number }[]
    thinner_pct?: number
    hardener_pct?: number
    print_color_sci?: { L: number; a: number; b: number }
    print_color_sce?: { L: number; a: number; b: number }
    delta_E_from_target?: number
    note?: string
  }>
}

export interface SampleResponse {
  sample_id: string
  round_id: string
  pattern_id: string
  sample_number: number
  base_color_sci: { L: number; a: number; b: number } | null
  base_color_sce: { L: number; a: number; b: number } | null
  base_material: string | null
  layers: Array<{
    layer_number: number
    ink_items: InkItem[]
    thinner_pct?: number
    hardener_pct?: number
    print_color_sci?: { L: number; a: number; b: number }
    print_color_sce?: { L: number; a: number; b: number }
    delta_E_from_target?: number
    note?: string
  }> | null
  final_delta_e?: number
  success_flag?: string
  success_notes?: string
  created_at: string
  updated_at: string
}

export const samplesApi = {
  getAll: (pattern_id?: string, round_id?: string) =>
    apiClient.get<SampleResponse[]>(`/api/samples${pattern_id ? `?pattern_id=${pattern_id}` : ''}${round_id ? `&round_id=${round_id}` : ''}`),

  getById: (id: string) =>
    apiClient.get<SampleResponse>(`/api/samples/${id}`),

  create: (round_id: string, data: SampleCreate) =>
    apiClient.post<SampleResponse>(`/api/samples/round/${round_id}`, data),

  update: (id: string, data: Partial<SampleCreate>) =>
    apiClient.put<SampleResponse>(`/api/samples/${id}`, data),

  delete: (id: string) =>
    apiClient.delete<void>(`/api/samples/${id}`),

  copyLayer: (sampleId: string, sourceSampleId: string, layerNumber: number) =>
    apiClient.post<SampleResponse>(`/api/samples/${sampleId}/copy-layer`, {
      source_sample_id: sourceSampleId,
      layer_number: layerNumber,
    }),
}
