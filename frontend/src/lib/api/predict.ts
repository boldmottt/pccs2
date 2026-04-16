import { apiClient } from './client'
import type { ColorXYZ, Layer } from '@/lib/types/project'

export interface PredictRequest {
  recipe: {
    layers: Layer[]
    thinnerAmount?: number
    hardenerAmount?: number
  }
  baseColor: ColorXYZ
}

export interface PredictResponse {
  kmPrediction: ColorXYZ
  mlCorrection: ColorXYZ | null
  mlConfidence: number
  finalPrediction: ColorXYZ
  deltaE: number
}

export const predictApi = {
  predict: (request: PredictRequest) =>
    apiClient.post<PredictResponse>('/api/predict', request),

  train: (historicalData: unknown[]) =>
    apiClient.post<{ status: string; samplesTrained: number }>('/api/predict/train', historicalData),

  health: () => apiClient.get<{ status: string; mlTrained: boolean }>('/api/predict/health'),
}
