import { apiClient } from './client'
import type { InkItem, Lab } from '@/lib/types/project'

export interface PredictLayerInput {
  ink_items?: InkItem[]
  k_over_s?: number
  thickness?: number
}

export interface PredictRequest {
  recipe: {
    layers: PredictLayerInput[]
    thinner_amount?: number
    hardener_amount?: number
  }
  base_color: Lab
}

export interface PredictResponse {
  km_prediction: Lab
  ml_correction?: Lab | null
  ml_confidence: number
  final_prediction: Lab
  delta_E: number
}

export const predictApi = {
  predict: (data: PredictRequest) => apiClient.post<PredictResponse>('/api/predict/', data),

  health: () => apiClient.get<{ status: string }>('/api/predict/health'),
}
